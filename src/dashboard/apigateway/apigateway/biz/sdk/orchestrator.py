"""Database-backed, lease-protected SDK generation orchestration."""

from __future__ import annotations

import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apigateway.apps.support.constants import (
    SDK_GENERATION_LANGUAGE_VALUES,
    SDKArtifactTypeEnum,
    SDKDistributorEnum,
    SDKGenerationStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk.artifacts import build_manifest
from apigateway.biz.sdk.builders import build_artifacts
from apigateway.biz.sdk.config import SDKLanguageConfig, get_sdk_generation_config
from apigateway.biz.sdk.exceptions import LegacySDKVersionConflict
from apigateway.biz.sdk.gateway_sdk import GatewaySDKHandler
from apigateway.biz.sdk.generator import generate_client, get_openapi_generator_version
from apigateway.biz.sdk.metrics import sdk_generation_metrics
from apigateway.biz.sdk.openapi import build_sdk_openapi, calculate_input_fingerprint, dump_sdk_openapi
from apigateway.biz.sdk.publishers import publish_native
from apigateway.biz.sdk.storage import (
    commit_generic_artifacts,
    generic_prefix,
    manifest_key,
    restore_generic_artifacts,
)
from apigateway.components.bkrepo import BKRepoComponent

if TYPE_CHECKING:
    from collections.abc import Callable

    from apigateway.core.models import ResourceVersion

LEASE_MINIMUM_SECONDS = 3600


@dataclass(frozen=True)
class GenerationClaim:
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
        status=SDKGenerationStatusEnum.SUCCESS.value,
    )
    if filename:
        queryset = queryset.filter(filename=filename)
    return queryset.exists()


def _reject_legacy_version_conflict(resource_version: ResourceVersion, language: str) -> None:
    sdk = GatewaySDK.objects.filter(
        gateway=resource_version.gateway,
        language=language,
        version_number=resource_version.version,
    ).first()
    if not sdk:
        return
    item_id = sdk.config.get("generation_item_id")
    if (
        item_id
        and SDKGenerationItem.objects.filter(
            id=item_id,
            task__resource_version=resource_version,
            artifacts__distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
            artifacts__filename="manifest.json",
            artifacts__status=SDKGenerationStatusEnum.SUCCESS.value,
        ).exists()
    ):
        return
    raise LegacySDKVersionConflict()


def _needs_native_retry(item: SDKGenerationItem, language_config: SDKLanguageConfig) -> bool:
    distributor = language_config.native_distributor
    return bool(distributor and not _has_successful_artifact(item, distributor))


@transaction.atomic
def create_or_resume_generation(
    resource_version: ResourceVersion,
    languages: list[str],
    operator: str | None,
    enqueue: Callable[[list[int]], None] | None = None,
) -> SDKGenerationTask:
    requested = _deduplicate_languages(languages)
    root_config = get_sdk_generation_config()
    disabled = set(requested).difference(root_config.enabled_languages)
    if disabled:
        raise ValueError(f"SDK generation languages are disabled: {sorted(disabled)}")
    for language in requested:
        _reject_legacy_version_conflict(resource_version, language)

    task, _ = SDKGenerationTask.objects.select_for_update().get_or_create(
        resource_version=resource_version,
        defaults={
            "gateway": resource_version.gateway,
            "status": SDKGenerationStatusEnum.PENDING.value,
            "created_by": operator,
            "updated_by": operator,
        },
    )
    now = timezone.now()
    item_ids = []
    for language in requested:
        language_config = root_config.for_resource_version(resource_version.gateway.name, resource_version, language)
        item, _ = SDKGenerationItem.objects.get_or_create(
            task=task,
            language=language,
            defaults={"created_by": operator, "updated_by": operator},
        )
        item.config_snapshot = {
            **language_config.build_fingerprint_payload(),
            "native_distributor": language_config.native_distributor,
        }
        if item.status == SDKGenerationStatusEnum.SUCCESS.value and _needs_native_retry(item, language_config):
            item.status = SDKGenerationStatusEnum.PARTIAL.value
        item.save(update_fields=["config_snapshot", "status", "updated_time"])
        if item.status in {
            SDKGenerationStatusEnum.PENDING.value,
            SDKGenerationStatusEnum.FAILED.value,
            SDKGenerationStatusEnum.PARTIAL.value,
        } or (
            item.status == SDKGenerationStatusEnum.RUNNING.value
            and (item.lease_expires_at is None or item.lease_expires_at <= now)
        ):
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
    now = timezone.now()
    eligible = item.status in {
        SDKGenerationStatusEnum.PENDING.value,
        SDKGenerationStatusEnum.FAILED.value,
        SDKGenerationStatusEnum.PARTIAL.value,
    } or (
        item.status == SDKGenerationStatusEnum.RUNNING.value
        and (item.lease_expires_at is None or item.lease_expires_at <= now)
    )
    if not eligible:
        return None

    timeout = get_sdk_generation_config().subprocess_timeout_seconds
    token = f"{celery_task_id}:{uuid.uuid4().hex}"
    item.status = SDKGenerationStatusEnum.RUNNING.value
    item.lease_token = token
    item.lease_expires_at = now + timedelta(seconds=max(LEASE_MINIMUM_SECONDS, timeout * 4))
    item.attempt_count = F("attempt_count") + 1
    item.started_at = now
    item.finished_at = None
    item.error_code = ""
    item.error_message = ""
    item.save(
        update_fields=[
            "status",
            "lease_token",
            "lease_expires_at",
            "attempt_count",
            "started_at",
            "finished_at",
            "error_code",
            "error_message",
            "updated_time",
        ]
    )
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
    return code, message[:1024]


def _persist_native_artifacts(item: SDKGenerationItem, published) -> None:
    for artifact in published:
        SDKArtifact.objects.update_or_create(
            item=item,
            distributor=artifact.distributor,
            filename=artifact.filename,
            defaults={
                "artifact_type": SDKArtifactTypeEnum.PACKAGE.value,
                "coordinate": artifact.coordinate,
                "url": artifact.url,
                "size": artifact.size,
                "sha256": artifact.sha256,
                "original_version": item.task.resource_version.version,
                "package_version": item.config_snapshot["package_version"],
                "status": SDKGenerationStatusEnum.SUCCESS.value,
            },
        )


def _record_generic_artifacts(item: SDKGenerationItem, count: int) -> None:
    sdk_generation_metrics.record_artifacts(
        item.language, SDKDistributorEnum.BKREPO_GENERIC.value, SDKGenerationStatusEnum.SUCCESS.value, count
    )


def _finish_item(claim: GenerationClaim, status: str, *, error: Exception | None = None) -> bool:
    updates: dict[str, Any] = {
        "status": status,
        "lease_token": "",
        "lease_expires_at": None,
        "finished_at": timezone.now(),
        "updated_time": timezone.now(),
    }
    if error:
        updates["error_code"], updates["error_message"] = _sanitize_error(error)
    else:
        updates["error_code"] = ""
        updates["error_message"] = ""
    return bool(SDKGenerationItem.objects.filter(id=claim.item_id, lease_token=claim.lease_token).update(**updates))


def _prepare_generation(item: SDKGenerationItem, claim: GenerationClaim):
    language_config = get_sdk_generation_config().for_resource_version(
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


def execute_generation_item(item_id: int, celery_task_id: str) -> str | None:
    claim = claim_generation_item(item_id, celery_task_id)
    if not claim:
        return None
    item = SDKGenerationItem.objects.select_related("task__gateway", "task__resource_version").get(id=item_id)
    generic_committed = False
    try:
        prepared = _prepare_generation(item, claim)
        if not prepared:
            return None
        language_config, document, tool_versions, fingerprint = prepared

        bkrepo = BKRepoComponent.default()
        if not bkrepo:
            raise ValueError("BKRepo Generic configuration is required")
        prefix = generic_prefix(
            item.task.gateway.name,
            item.language,
            item.task.resource_version.version,
            fingerprint,
        )
        with tempfile.TemporaryDirectory(prefix="sdk-generation-") as directory:
            workspace = Path(directory)
            if bkrepo.get_generic_file_metadata(manifest_key(prefix)) is not None:
                with sdk_generation_metrics.observe_phase(item.language, "restore"):
                    manifest, artifacts = restore_generic_artifacts(item, bkrepo, workspace / "restored")
                generic_committed = True
            else:
                spec_path = workspace / "openapi.json"
                spec_path.write_text(dump_sdk_openapi(document))
                source_dir = workspace / "source"
                with sdk_generation_metrics.observe_phase(item.language, "generate"):
                    generate_client(spec_path, source_dir, language_config)
                with sdk_generation_metrics.observe_phase(item.language, "build"):
                    artifacts = build_artifacts(item.language, source_dir, workspace / "dist", language_config)
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
                generic_committed = True

            if not _has_successful_artifact(item, SDKDistributorEnum.BKREPO_GENERIC.value, filename="manifest.json"):
                raise ValueError("Generic manifest is not committed")
            GatewaySDKHandler.upsert_generation_projection(item, language_config, manifest)
            with sdk_generation_metrics.observe_phase(item.language, "native_publish"):
                published = publish_native(item.language, artifacts, language_config)
            _persist_native_artifacts(item, published)
            for artifact in published:
                sdk_generation_metrics.record_artifacts(item.language, artifact.distributor, "success")
            GatewaySDKHandler.upsert_generation_projection(item, language_config, manifest)

        if _finish_item(claim, SDKGenerationStatusEnum.SUCCESS.value):
            sdk_generation_metrics.record_result(item.language, SDKGenerationStatusEnum.SUCCESS.value)
    except Exception as error:
        status = SDKGenerationStatusEnum.PARTIAL.value if generic_committed else SDKGenerationStatusEnum.FAILED.value
        if _finish_item(claim, status, error=error):
            sdk_generation_metrics.record_result(item.language, status)
    refresh_task_status(item.task_id)
    item.refresh_from_db()
    return item.status


@transaction.atomic
def retry_generation_task(
    task: SDKGenerationTask,
    enqueue: Callable[[list[int]], None] | None = None,
) -> SDKGenerationTask:
    now = timezone.now()
    item_ids = list(
        task.items.filter(
            Q(status__in=[SDKGenerationStatusEnum.FAILED.value, SDKGenerationStatusEnum.PARTIAL.value])
            | Q(status=SDKGenerationStatusEnum.RUNNING.value)
            & (Q(lease_expires_at__lte=now) | Q(lease_expires_at__isnull=True))
        ).values_list("id", flat=True)
    )
    if enqueue and item_ids:
        transaction.on_commit(partial(enqueue, item_ids.copy()))
    return task


def refresh_task_status(task_id: int) -> str:
    statuses = list(SDKGenerationItem.objects.filter(task_id=task_id).values_list("status", flat=True))
    if not statuses or all(status == SDKGenerationStatusEnum.PENDING.value for status in statuses):
        status = SDKGenerationStatusEnum.PENDING.value
    elif all(status == SDKGenerationStatusEnum.SUCCESS.value for status in statuses):
        status = SDKGenerationStatusEnum.SUCCESS.value
    elif any(status == SDKGenerationStatusEnum.RUNNING.value for status in statuses):
        status = SDKGenerationStatusEnum.RUNNING.value
    elif all(status == SDKGenerationStatusEnum.FAILED.value for status in statuses):
        status = SDKGenerationStatusEnum.FAILED.value
    else:
        status = SDKGenerationStatusEnum.PARTIAL.value
    SDKGenerationTask.objects.filter(id=task_id).update(status=status, updated_time=timezone.now())
    return status


def serialize_generation_task(task: SDKGenerationTask) -> dict[str, Any]:
    items = task.items.prefetch_related("artifacts").order_by("id")
    return {
        "id": task.id,
        "status": task.status,
        "resource_version": {
            "id": task.resource_version_id,
            "version": task.resource_version.version,
        },
        "items": [
            {
                "id": item.id,
                "language": item.language,
                "status": item.status,
                "attempt_count": item.attempt_count,
                "error": {"code": item.error_code, "message": item.error_message}
                if item.error_code or item.error_message
                else None,
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
                    for artifact in item.artifacts.all()
                ],
            }
            for item in items
        ],
    }
