"""Database-backed, lease-protected SDK generation orchestration."""

from __future__ import annotations

import logging
import re
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apigateway.apps.support.constants import (
    SDK_GENERATION_LANGUAGE_VALUES,
    SDKArtifactStatusEnum,
    SDKArtifactTypeEnum,
    SDKDistributorEnum,
    SDKGenerationItemStatusEnum,
    SDKGenerationTaskStatusEnum,
    SDKNativePublicationStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk.artifacts import build_manifest
from apigateway.biz.sdk.builders import build_artifacts
from apigateway.biz.sdk.config import get_sdk_generation_policy, get_sdk_worker_config
from apigateway.biz.sdk.exceptions import SDKConfigurationError, SDKGenerateError, SDKGenerationError
from apigateway.biz.sdk.gateway_sdk import ensure_gateway_sdk_projection
from apigateway.biz.sdk.generator import generate_client, get_openapi_generator_version
from apigateway.biz.sdk.metrics import sdk_generation_metrics
from apigateway.biz.sdk.openapi import build_sdk_openapi, calculate_input_fingerprint, dump_sdk_openapi
from apigateway.biz.sdk.publishers import publish_native
from apigateway.biz.sdk.publishers.common import redact_sensitive_text
from apigateway.biz.sdk.storage import (
    commit_generic_artifacts,
    delete_incomplete_artifacts,
    generic_prefix,
    manifest_key,
    restore_generic_artifacts,
)
from apigateway.components.bkrepo import BKRepoComponent

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from apigateway.core.models import ResourceVersion

LEASE_MINIMUM_SECONDS = 3600
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenerationClaim:
    item_id: int
    lease_token: str


@dataclass(frozen=True)
class ItemExecutionResult:
    status: str
    retry_delay_seconds: int | None


@dataclass(frozen=True)
class NativePublicationClaim:
    item_id: int
    lease_token: str


def _deduplicate_languages(languages: list[str]) -> list[str]:
    result = list(dict.fromkeys(languages))
    if not result:
        raise ValueError("at least one SDK language is required")
    invalid = set(result).difference(SDK_GENERATION_LANGUAGE_VALUES)
    if invalid:
        raise ValueError(f"unsupported SDK generation languages: {sorted(invalid)}")
    return result


def _has_successful_artifact(item: SDKGenerationItem, distributor: str, *, filename: str | None = None) -> bool:
    queryset = item.artifacts.filter(
        distributor=distributor,
        status=SDKArtifactStatusEnum.SUCCESS.value,
    )
    if filename:
        queryset = queryset.filter(filename=filename)
    return queryset.exists()


@transaction.atomic
def create_or_resume_generation(
    resource_version: ResourceVersion,
    languages: list[str],
    operator: str | None,
    enqueue: Callable[[list[int]], None] | None = None,
) -> SDKGenerationTask:
    requested = _deduplicate_languages(languages)
    policy = get_sdk_generation_policy()
    disabled = set(requested).difference(policy.languages)
    if disabled:
        raise ValueError(f"SDK generation languages are disabled: {sorted(disabled)}")

    task, _ = SDKGenerationTask.objects.select_for_update().get_or_create(
        resource_version=resource_version,
        defaults={
            "gateway": resource_version.gateway,
            "status": SDKGenerationTaskStatusEnum.PENDING.value,
            "created_by": operator,
            "updated_by": operator,
        },
    )
    item_ids = []
    for language in requested:
        language_config = policy.for_resource_version(resource_version.gateway.name, resource_version, language)
        item, created = SDKGenerationItem.objects.get_or_create(
            task=task,
            language=language,
            defaults={
                "created_by": operator,
                "updated_by": operator,
                "config_snapshot": {
                    **language_config.build_fingerprint_payload(),
                    "native_distributor": language_config.native_distributor,
                },
                "native_status": (
                    SDKNativePublicationStatusEnum.PENDING.value
                    if language_config.native_distributor
                    else SDKNativePublicationStatusEnum.NOT_REQUIRED.value
                ),
            },
        )
        if item.status == SDKGenerationItemStatusEnum.SUCCESS.value:
            continue
        legacy_sdk_exists = GatewaySDK.objects.filter(
            gateway=resource_version.gateway,
            language=language,
            version_number=resource_version.version,
        ).exists()
        if legacy_sdk_exists and not item.gateway_sdk_id:
            item.native_status = SDKNativePublicationStatusEnum.NOT_REQUIRED.value
            item.save(update_fields=["native_status", "updated_time"])
            ensure_gateway_sdk_projection(item)
            continue
        if item.status == SDKGenerationItemStatusEnum.RUNNING.value:
            if item.lease_expires_at is None or item.lease_expires_at > timezone.now():
                continue
            item.status = SDKGenerationItemStatusEnum.PENDING.value
            item.lease_token = ""
            item.lease_expires_at = None
            item.save(update_fields=["status", "lease_token", "lease_expires_at", "updated_time"])
        elif item.status == SDKGenerationItemStatusEnum.FAILED.value:
            if not item.error_retryable:
                continue
            item.status = SDKGenerationItemStatusEnum.PENDING.value
            item.attempt_cycle_count = 0
            item.next_attempt_at = None
            item.save(update_fields=["status", "attempt_cycle_count", "next_attempt_at", "updated_time"])
        elif not created and item.next_attempt_at and item.next_attempt_at > timezone.now():
            continue
        item_ids.append(item.id)

    refresh_task_status(task.id)
    task.refresh_from_db()
    if enqueue and item_ids:
        transaction.on_commit(partial(enqueue, item_ids.copy()))
    return task


@transaction.atomic
def claim_generation_item(item_id: int, celery_task_id: str) -> GenerationClaim | None:
    item = SDKGenerationItem.objects.select_for_update().filter(id=item_id).first()
    if not item:
        return None
    if not get_sdk_generation_policy().enabled:
        return None
    now = timezone.now()
    eligible = (
        item.status == SDKGenerationItemStatusEnum.PENDING.value
        and (item.next_attempt_at is None or item.next_attempt_at <= now)
    ) or (
        item.status == SDKGenerationItemStatusEnum.RUNNING.value
        and (item.lease_expires_at is None or item.lease_expires_at <= now)
    )
    if not eligible:
        return None

    timeout = settings.SDK_GENERATION["subprocess_timeout_seconds"]
    token = f"{celery_task_id}:{uuid.uuid4().hex}"
    item.status = SDKGenerationItemStatusEnum.RUNNING.value
    item.lease_token = token
    item.lease_expires_at = now + timedelta(seconds=max(LEASE_MINIMUM_SECONDS, timeout * 4))
    item.attempt_count = F("attempt_count") + 1
    item.attempt_cycle_count = F("attempt_cycle_count") + 1
    item.next_attempt_at = None
    item.started_at = now
    item.finished_at = None
    item.error_code = ""
    item.error_message = ""
    item.error_retryable = False
    item.save(
        update_fields=[
            "status",
            "lease_token",
            "lease_expires_at",
            "attempt_count",
            "attempt_cycle_count",
            "next_attempt_at",
            "started_at",
            "finished_at",
            "error_code",
            "error_message",
            "error_retryable",
            "updated_time",
        ]
    )
    refresh_task_status(item.task_id)
    return GenerationClaim(item.id, token)


def _sanitize_error(error: Exception) -> tuple[str, str]:
    code = str(getattr(error, "code", "generation_failed"))[:64]
    message = re.sub(r"\s+", " ", str(error)).strip() or error.__class__.__name__
    secrets = [
        getattr(settings, "BKREPO_PASSWORD", ""),
        *[config.get("password", "") for config in (getattr(settings, "PYPI_MIRRORS_CONFIG", {}) or {}).values()],
        *[config.get("password", "") for config in (getattr(settings, "MAVEN_MIRRORS_CONFIG", {}) or {}).values()],
    ]
    for secret in secrets:
        if secret:
            message = message.replace(secret, "***")
    return code, redact_sensitive_text(message, tuple(secrets))[:1024]


def _persist_native_artifacts(item: SDKGenerationItem, published) -> None:
    for artifact in published:
        SDKArtifact.objects.update_or_create(
            item=item,
            distributor=artifact.distributor,
            filename=artifact.filename,
            defaults={
                "artifact_type": artifact.artifact_type,
                "coordinate": artifact.coordinate,
                "url": artifact.url,
                "size": artifact.size,
                "sha256": artifact.sha256,
                "original_version": item.task.resource_version.version,
                "package_version": item.config_snapshot["package_version"],
                "status": SDKArtifactStatusEnum.SUCCESS.value,
            },
        )


def _record_generic_artifacts(item: SDKGenerationItem, count: int) -> None:
    sdk_generation_metrics.record_artifacts(
        item.language, SDKDistributorEnum.BKREPO_GENERIC.value, SDKArtifactStatusEnum.SUCCESS.value, count
    )


def finish_generation_item(
    claim: GenerationClaim,
    status: str,
    *,
    error: Exception | None = None,
    next_attempt_at: datetime | None = None,
) -> bool:
    updates: dict[str, Any] = {
        "status": status,
        "lease_token": "",
        "lease_expires_at": None,
        "next_attempt_at": next_attempt_at,
        "finished_at": None if status == SDKGenerationItemStatusEnum.PENDING.value else timezone.now(),
        "updated_time": timezone.now(),
    }
    if error:
        updates["error_code"], updates["error_message"] = _sanitize_error(error)
        updates["error_retryable"] = isinstance(error, SDKGenerationError) and error.retryable
    else:
        updates["error_code"] = ""
        updates["error_message"] = ""
        updates["error_retryable"] = False
    return bool(SDKGenerationItem.objects.filter(id=claim.item_id, lease_token=claim.lease_token).update(**updates))


def _classify_generation_error(error: Exception) -> SDKGenerationError:
    if isinstance(error, SDKGenerationError):
        return error
    if isinstance(error, (subprocess.TimeoutExpired, requests.Timeout, requests.ConnectionError)):
        return SDKGenerationError("temporary_network", str(error) or "temporary network failure", retryable=True)
    if isinstance(error, requests.HTTPError):
        status_code = error.response.status_code if error.response is not None else None
        retryable = status_code == 429 or (status_code is not None and status_code >= 500)
        code = "remote_service_unavailable" if retryable else "remote_request_failed"
        return SDKGenerationError(code, str(error) or code, retryable=retryable)
    if isinstance(error, SDKConfigurationError):
        return SDKGenerationError("configuration_error", str(error))
    return SDKGenerationError("generation_failed", str(error) or error.__class__.__name__)


def _renew_claim(claim: GenerationClaim) -> bool:
    timeout = settings.SDK_GENERATION["subprocess_timeout_seconds"]
    return bool(
        SDKGenerationItem.objects.filter(
            id=claim.item_id,
            lease_token=claim.lease_token,
            status=SDKGenerationItemStatusEnum.RUNNING.value,
        ).update(
            lease_expires_at=timezone.now() + timedelta(seconds=max(LEASE_MINIMUM_SECONDS, timeout * 4)),
            updated_time=timezone.now(),
        )
    )


def _require_claim(claim: GenerationClaim) -> None:
    if not _renew_claim(claim):
        raise SDKGenerateError("lease_lost", "SDK generation lease was lost")


def _record_lost_claim(item: SDKGenerationItem, claim: GenerationClaim) -> None:
    logger.warning("SDK generation lease lost for item %s with claim %s", item.id, claim.lease_token)
    sdk_generation_metrics.record_result(item.language, "failed", "lease_lost")


@transaction.atomic
def claim_native_publication(item_id: int, celery_task_id: str) -> NativePublicationClaim | None:
    item = SDKGenerationItem.objects.select_for_update().filter(id=item_id).first()
    if not item or not get_sdk_generation_policy().enabled or item.status != SDKGenerationItemStatusEnum.SUCCESS.value:
        return None
    now = timezone.now()
    eligible = (
        item.native_status == SDKNativePublicationStatusEnum.PENDING.value
        and (item.native_next_attempt_at is None or item.native_next_attempt_at <= now)
    ) or (
        item.native_status == SDKNativePublicationStatusEnum.RUNNING.value
        and (item.native_lease_expires_at is None or item.native_lease_expires_at <= now)
    )
    if not eligible:
        return None

    timeout = settings.SDK_GENERATION["subprocess_timeout_seconds"]
    token = f"{celery_task_id[:24]}:{uuid.uuid4().hex}"
    item.native_status = SDKNativePublicationStatusEnum.RUNNING.value
    item.native_lease_token = token
    item.native_lease_expires_at = now + timedelta(seconds=max(LEASE_MINIMUM_SECONDS, timeout * 4))
    item.native_attempt_count = F("native_attempt_count") + 1
    item.native_attempt_cycle_count = F("native_attempt_cycle_count") + 1
    item.native_next_attempt_at = None
    item.native_error_code = ""
    item.native_error_message = ""
    item.save(
        update_fields=[
            "native_status",
            "native_lease_token",
            "native_lease_expires_at",
            "native_attempt_count",
            "native_attempt_cycle_count",
            "native_next_attempt_at",
            "native_error_code",
            "native_error_message",
            "updated_time",
        ]
    )
    return NativePublicationClaim(item.id, token)


def finish_native_publication(
    claim: NativePublicationClaim,
    status: str,
    *,
    error: Exception | None = None,
    next_attempt_at: datetime | None = None,
) -> bool:
    updates: dict[str, Any] = {
        "native_status": status,
        "native_lease_token": "",
        "native_lease_expires_at": None,
        "native_next_attempt_at": next_attempt_at,
        "updated_time": timezone.now(),
    }
    if error:
        updates["native_error_code"], updates["native_error_message"] = _sanitize_error(error)
    else:
        updates["native_error_code"] = ""
        updates["native_error_message"] = ""
    return bool(
        SDKGenerationItem.objects.filter(id=claim.item_id, native_lease_token=claim.lease_token).update(**updates)
    )


def _renew_native_claim(claim: NativePublicationClaim) -> bool:
    timeout = settings.SDK_GENERATION["subprocess_timeout_seconds"]
    return bool(
        SDKGenerationItem.objects.filter(
            id=claim.item_id,
            native_lease_token=claim.lease_token,
            native_status=SDKNativePublicationStatusEnum.RUNNING.value,
        ).update(
            native_lease_expires_at=timezone.now() + timedelta(seconds=max(LEASE_MINIMUM_SECONDS, timeout * 4)),
            updated_time=timezone.now(),
        )
    )


def _require_native_claim(claim: NativePublicationClaim) -> None:
    if not _renew_native_claim(claim):
        raise SDKGenerateError("native_lease_lost", "SDK native publication lease was lost")


def _prepare_generation(item: SDKGenerationItem, claim: GenerationClaim):
    language_config = get_sdk_worker_config().for_resource_version(
        item.task.gateway.name, item.task.resource_version, item.language
    )
    with sdk_generation_metrics.observe_phase(item.language, "openapi"):
        tool_versions = {"openapi-generator": get_openapi_generator_version()}
        document = build_sdk_openapi(item.task.resource_version)
        fingerprint = calculate_input_fingerprint(document, language_config, tool_versions)
    config_snapshot = {
        **language_config.build_fingerprint_payload(),
        "native_distributor": language_config.native_distributor,
    }
    if not SDKGenerationItem.objects.filter(id=item.id, lease_token=claim.lease_token).update(
        input_fingerprint=fingerprint,
        config_snapshot=config_snapshot,
    ):
        return None
    item.input_fingerprint = fingerprint
    item.config_snapshot = config_snapshot
    return language_config, document, tool_versions, fingerprint


def _complete_failed_execution(item: SDKGenerationItem, claim: GenerationClaim, error: Exception) -> int | None:
    classified = _classify_generation_error(error)
    item.refresh_from_db(fields=["attempt_cycle_count"])
    retry_delay = None
    next_attempt_at = None
    policy = get_sdk_generation_policy()
    if classified.retryable and item.attempt_cycle_count <= len(policy.retry_delays):
        status = SDKGenerationItemStatusEnum.PENDING.value
        retry_delay = policy.retry_delays[item.attempt_cycle_count - 1]
        next_attempt_at = timezone.now() + timedelta(seconds=retry_delay)
    else:
        status = SDKGenerationItemStatusEnum.FAILED.value
    if not finish_generation_item(claim, status, error=classified, next_attempt_at=next_attempt_at):
        _record_lost_claim(item, claim)
        return None
    sdk_generation_metrics.record_result(item.language, status, classified.code)
    logger.warning(
        "SDK generation item failed",
        extra={
            "sdk_item_id": item.id,
            "sdk_task_id": item.task_id,
            "language": item.language,
            "error_class": classified.code,
            "retryable": classified.retryable,
        },
    )
    return retry_delay


def execute_generation_item(item_id: int, celery_task_id: str) -> ItemExecutionResult | None:  # noqa: PLR0915
    claim = claim_generation_item(item_id, celery_task_id)
    if not claim:
        return None
    item = SDKGenerationItem.objects.select_related("task__gateway", "task__resource_version").get(id=item_id)
    try:
        prepared = _prepare_generation(item, claim)
        if not prepared:
            _record_lost_claim(item, claim)
            refresh_task_status(item.task_id)
            item.refresh_from_db()
            return ItemExecutionResult(item.status, None)
        language_config, document, tool_versions, fingerprint = prepared
        _require_claim(claim)

        bkrepo = BKRepoComponent.default()
        if not bkrepo:
            raise ValueError("BKRepo Generic configuration is required")
        prefix = generic_prefix(
            item.task.gateway.name,
            item.language,
            item.task.resource_version.version,
            fingerprint,
            item.id,
        )
        with tempfile.TemporaryDirectory(prefix="sdk-generation-") as directory:
            workspace = Path(directory)
            if bkrepo.get_generic_file_metadata(manifest_key(prefix)) is not None:
                with sdk_generation_metrics.observe_phase(item.language, "restore"):
                    manifest, artifacts = restore_generic_artifacts(item, bkrepo, workspace / "restored")
            else:
                delete_incomplete_artifacts(item, bkrepo, expected_lease_token=claim.lease_token)
                spec_path = workspace / "openapi.json"
                spec_path.write_text(dump_sdk_openapi(document))
                source_dir = workspace / "source"
                with sdk_generation_metrics.observe_phase(item.language, "generate"):
                    generate_client(spec_path, source_dir, language_config)
                _require_claim(claim)
                with sdk_generation_metrics.observe_phase(item.language, "build"):
                    artifacts = build_artifacts(item.language, source_dir, workspace / "dist", language_config)
                _require_claim(claim)
                manifest = build_manifest(
                    item.task.gateway.name,
                    item.task.resource_version.version,
                    item.language,
                    language_config.package_version,
                    fingerprint,
                    tool_versions,
                    artifacts,
                )
                with sdk_generation_metrics.observe_phase(item.language, "generic_publish"):
                    committed = commit_generic_artifacts(item, bkrepo, manifest, artifacts)
                _record_generic_artifacts(item, len(committed))

            if not _has_successful_artifact(item, SDKDistributorEnum.BKREPO_GENERIC.value, filename="manifest.json"):
                raise ValueError("Generic manifest is not committed")
            _require_claim(claim)
            ensure_gateway_sdk_projection(item)

        status = SDKGenerationItemStatusEnum.SUCCESS.value
        retry_delay = None
        if finish_generation_item(claim, status):
            sdk_generation_metrics.record_result(item.language, status, "none")
            logger.info(
                "SDK generation item completed",
                extra={"sdk_item_id": item.id, "sdk_task_id": item.task_id, "language": item.language},
            )
        else:
            _record_lost_claim(item, claim)
    except Exception as error:
        retry_delay = _complete_failed_execution(item, claim, error)
    refresh_task_status(item.task_id)
    item.refresh_from_db()
    return ItemExecutionResult(item.status, retry_delay)


def _complete_failed_native_publication(
    item: SDKGenerationItem, claim: NativePublicationClaim, error: Exception
) -> int | None:
    classified = _classify_generation_error(error)
    item.refresh_from_db(fields=["native_attempt_cycle_count"])
    retry_delay = None
    next_attempt_at = None
    policy = get_sdk_generation_policy()
    if classified.retryable and item.native_attempt_cycle_count <= len(policy.retry_delays):
        status = SDKNativePublicationStatusEnum.PENDING.value
        retry_delay = policy.retry_delays[item.native_attempt_cycle_count - 1]
        next_attempt_at = timezone.now() + timedelta(seconds=retry_delay)
    else:
        status = SDKNativePublicationStatusEnum.FAILED.value
    if not finish_native_publication(claim, status, error=classified, next_attempt_at=next_attempt_at):
        logger.warning("SDK native publication lease lost for item %s", item.id)
        return None
    logger.warning(
        "SDK native publication failed",
        extra={
            "sdk_item_id": item.id,
            "sdk_task_id": item.task_id,
            "language": item.language,
            "error_class": classified.code,
            "retryable": classified.retryable,
        },
    )
    return retry_delay


def execute_native_publication(item_id: int, celery_task_id: str) -> ItemExecutionResult | None:
    claim = claim_native_publication(item_id, celery_task_id)
    if not claim:
        return None
    item = SDKGenerationItem.objects.select_related("task__gateway", "task__resource_version").get(id=item_id)
    try:
        worker_config = get_sdk_worker_config()
        language_config = worker_config.for_resource_version(
            item.task.gateway.name, item.task.resource_version, item.language
        )
        expected_distributor = item.config_snapshot.get("native_distributor")
        if not expected_distributor or language_config.native_distributor != expected_distributor:
            raise SDKConfigurationError("configured native SDK repository is unavailable")
        bkrepo = BKRepoComponent.default()
        if not bkrepo:
            raise SDKConfigurationError("BKRepo Generic configuration is required")
        _require_native_claim(claim)
        with tempfile.TemporaryDirectory(prefix="sdk-native-publication-") as directory:
            _, artifacts = restore_generic_artifacts(item, bkrepo, Path(directory))
            _require_native_claim(claim)
            with sdk_generation_metrics.observe_phase(item.language, "native_publish"):
                published = publish_native(item.language, artifacts, language_config)
            _require_native_claim(claim)
            _persist_native_artifacts(item, published)
            for artifact in published:
                sdk_generation_metrics.record_artifacts(item.language, artifact.distributor, "success")
        retry_delay = None
        if not finish_native_publication(claim, SDKNativePublicationStatusEnum.SUCCESS.value):
            logger.warning("SDK native publication lease lost for item %s", item.id)
    except Exception as error:
        retry_delay = _complete_failed_native_publication(item, claim, error)
    item.refresh_from_db()
    return ItemExecutionResult(item.native_status, retry_delay)


@transaction.atomic
def refresh_task_status(task_id: int) -> str:
    SDKGenerationTask.objects.select_for_update().get(id=task_id)
    statuses = list(SDKGenerationItem.objects.filter(task_id=task_id).values_list("status", flat=True))
    status_set = set(statuses)
    if not statuses or status_set == {SDKGenerationItemStatusEnum.PENDING.value}:
        status = SDKGenerationTaskStatusEnum.PENDING.value
    elif SDKGenerationItemStatusEnum.RUNNING.value in status_set or (
        SDKGenerationItemStatusEnum.PENDING.value in status_set and len(status_set) > 1
    ):
        status = SDKGenerationTaskStatusEnum.RUNNING.value
    elif status_set == {SDKGenerationItemStatusEnum.SUCCESS.value}:
        status = SDKGenerationTaskStatusEnum.SUCCESS.value
    elif status_set == {SDKGenerationItemStatusEnum.FAILED.value}:
        status = SDKGenerationTaskStatusEnum.FAILED.value
    else:
        status = SDKGenerationTaskStatusEnum.PARTIAL.value
    SDKGenerationTask.objects.filter(id=task_id).update(status=status, updated_time=timezone.now())
    return status


def serialize_generation_task(task: SDKGenerationTask) -> dict[str, Any]:
    items = task.items.all()
    preferred_types = {
        "python": SDKArtifactTypeEnum.WHEEL.value,
        "java": SDKArtifactTypeEnum.DISTRIBUTION_ZIP.value,
        "go": SDKArtifactTypeEnum.GO_ZIP.value,
        "javascript": SDKArtifactTypeEnum.NPM_TGZ.value,
    }
    serialized_items = []
    for item in items:
        artifact_rows = [
            artifact
            for artifact in item.artifacts.all()
            if artifact.status == SDKArtifactStatusEnum.SUCCESS.value
            and artifact.artifact_type != SDKArtifactTypeEnum.MANIFEST.value
        ]
        preferred = next(
            (artifact for artifact in artifact_rows if artifact.artifact_type == preferred_types.get(item.language)),
            artifact_rows[0] if artifact_rows else None,
        )
        serialized_items.append(
            {
                "id": item.id,
                "language": item.language,
                "status": item.status,
                "native_status": item.native_status,
                "attempt_count": item.attempt_count,
                "error": {"code": item.error_code, "message": item.error_message}
                if item.error_code or item.error_message
                else None,
                "native_error": {"code": item.native_error_code, "message": item.native_error_message}
                if item.native_error_code or item.native_error_message
                else None,
                "download_url": preferred.url if preferred else (item.gateway_sdk.url if item.gateway_sdk_id else ""),
                "artifacts": [
                    {
                        "distributor": artifact.distributor,
                        "type": artifact.artifact_type,
                        "filename": artifact.filename,
                        "url": artifact.url,
                        "coordinate": artifact.coordinate,
                        "size": artifact.size,
                        "sha256": artifact.sha256,
                        "status": artifact.status,
                    }
                    for artifact in artifact_rows
                ],
            }
        )
    return {
        "id": task.id,
        "status": task.status,
        "resource_version": {
            "id": task.resource_version_id,
            "version": task.resource_version.version,
        },
        "items": serialized_items,
    }
