import logging
from datetime import timedelta
from pathlib import Path

import pytest
from blue_krill.storages.blobstore.exceptions import ObjectAlreadyExists
from ddf import G
from django.utils import timezone

from apigateway.apps.support.constants import SDKDistributorEnum, SDKGenerationStatusEnum
from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.sdk.artifacts import create_built_artifact
from apigateway.biz.sdk.exceptions import LegacySDKVersionConflict, SDKGenerateError
from apigateway.biz.sdk.orchestrator import (
    claim_generation_item,
    create_or_resume_generation,
    execute_generation_item,
    refresh_task_status,
    retry_generation_task,
    serialize_generation_task,
)

pytestmark = pytest.mark.django_db


class FakeBKRepo:
    def __init__(self):
        self.files = {}

    def upload_generic_file(self, filepath, key, allow_overwrite=True):
        if key in self.files and not allow_overwrite:
            raise ObjectAlreadyExists("exists")
        self.files[key] = Path(filepath).read_bytes()

    def download_generic_file(self, key, filepath):
        Path(filepath).write_bytes(self.files[key])
        return Path(filepath)

    def get_generic_file_metadata(self, key):
        return {} if key in self.files else None

    def delete_generic_file(self, key):
        self.files.pop(key, None)

    def generate_generic_download_url(self, key):
        return f"https://repo/{key}"


@pytest.fixture(autouse=True)
def sdk_settings(settings, fake_resource_version):
    fake_resource_version.version = "1.2.3"
    fake_resource_version.save(update_fields=["version"])
    settings.BKREPO_ENDPOINT_URL = "https://repo"
    settings.BKREPO_USERNAME = "user"
    settings.BKREPO_PASSWORD = "password"
    settings.BKREPO_PROJECT = "project"
    settings.BKREPO_GENERIC_BUCKET = "generic"
    settings.PYPI_MIRRORS_CONFIG = {"default": {}}
    settings.MAVEN_MIRRORS_CONFIG = {"default": {}}


def test_create_deduplicates_languages_and_enqueues_on_commit(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        task = create_or_resume_generation(fake_resource_version, ["python", "go", "python"], "admin", enqueue)

    assert list(task.items.values_list("language", flat=True).order_by("id")) == ["python", "go"]
    enqueue.assert_called_once_with(list(task.items.values_list("id", flat=True).order_by("id")))


def test_create_keeps_each_request_and_active_item_independent(fake_resource_version):
    first_task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    first_item = first_task.items.get()
    first_item.status = SDKGenerationStatusEnum.RUNNING.value
    first_item.lease_token = "active"
    first_item.lease_expires_at = timezone.now() + timedelta(minutes=5)
    first_item.config_snapshot = {"request": "first"}
    first_item.save(update_fields=["status", "lease_token", "lease_expires_at", "config_snapshot"])

    second_task = create_or_resume_generation(fake_resource_version, ["go"], "admin")

    first_item.refresh_from_db()
    assert second_task.id != first_task.id
    assert list(second_task.items.values_list("language", flat=True)) == ["go"]
    assert first_item.status == SDKGenerationStatusEnum.RUNNING.value
    assert first_item.lease_token == "active"
    assert first_item.config_snapshot == {"request": "first"}


def test_claim_excludes_active_lease_and_takes_expired_lease(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    first = claim_generation_item(item.id, "celery-1")

    assert first is not None
    assert claim_generation_item(item.id, "celery-2") is None

    item.refresh_from_db()
    item.lease_expires_at = timezone.now() - timedelta(seconds=1)
    item.save(update_fields=["lease_expires_at"])
    second = claim_generation_item(item.id, "celery-2")
    assert second is not None
    assert second.lease_token != first.lease_token


def test_claim_marks_parent_task_running(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()

    assert claim_generation_item(item.id, "celery-1") is not None

    task.refresh_from_db()
    assert task.status == SDKGenerationStatusEnum.RUNNING.value


def test_refresh_reports_pending_when_successful_task_adds_pending_language(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    task.items.filter(language="python").update(status=SDKGenerationStatusEnum.SUCCESS.value)

    assert refresh_task_status(task.id) == SDKGenerationStatusEnum.PENDING.value


def test_refresh_and_serialization_report_partial_task(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    task.items.filter(language="python").update(status=SDKGenerationStatusEnum.SUCCESS.value)
    task.items.filter(language="go").update(
        status=SDKGenerationStatusEnum.FAILED.value, error_code="build_failed", error_message="failed"
    )

    assert refresh_task_status(task.id) == SDKGenerationStatusEnum.PARTIAL.value
    task.refresh_from_db()
    payload = serialize_generation_task(task)
    assert payload["status"] == "partial"
    assert payload["items"][1]["error"] == {"code": "build_failed", "message": "failed"}


def test_legacy_sdk_coordinate_is_immutable(fake_gateway, fake_resource_version):
    sdk = G(
        GatewaySDK,
        gateway=fake_gateway,
        resource_version=fake_resource_version,
        language="python",
        version_number=fake_resource_version.version,
        schema=None,
    )
    sdk.config = {}
    sdk.save(update_fields=["_config"])

    with pytest.raises(LegacySDKVersionConflict):
        create_or_resume_generation(fake_resource_version, ["python"], "admin")


def _patch_pipeline(mocker, bkrepo, *, publisher_side_effect=None):
    mocker.patch("apigateway.biz.sdk.orchestrator.BKRepoComponent.default", return_value=bkrepo)
    mocker.patch("apigateway.biz.sdk.orchestrator.get_openapi_generator_version", return_value="7.23.0")
    mocker.patch(
        "apigateway.biz.sdk.orchestrator.build_sdk_openapi",
        return_value={"openapi": "3.0.1", "info": {"title": "demo", "version": "1.2.3"}, "paths": {}},
    )
    mocker.patch("apigateway.biz.sdk.orchestrator.dump_sdk_openapi", return_value="{}")
    mocker.patch("apigateway.biz.sdk.orchestrator.generate_client")

    def fake_build(_language, _source, output, _config):
        output.mkdir(parents=True, exist_ok=True)
        path = output / "demo.whl"
        path.write_bytes(b"wheel")
        return [create_built_artifact("wheel", path, allowed_roots=(output,))]

    build = mocker.patch("apigateway.biz.sdk.orchestrator.build_artifacts", side_effect=fake_build)
    publish = mocker.patch("apigateway.biz.sdk.orchestrator.publish_native", side_effect=publisher_side_effect)
    return build, publish


def test_execute_commits_generic_before_success_and_projects_sdk(fake_gateway, fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _patch_pipeline(mocker, bkrepo)

    assert execute_generation_item(item.id, "celery-1") == SDKGenerationStatusEnum.SUCCESS.value

    item.refresh_from_db()
    assert item.artifacts.filter(
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        filename="manifest.json",
        status=SDKGenerationStatusEnum.SUCCESS.value,
    ).exists()
    sdk = GatewaySDK.objects.get(gateway=fake_gateway, language="python", version_number=fake_resource_version.version)
    assert sdk.config["generation_item_id"] == item.id
    assert sdk.config["artifacts"]


def test_partial_native_retry_restores_generic_without_rebuild(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    build, publish = _patch_pipeline(
        mocker,
        bkrepo,
        publisher_side_effect=SDKGenerateError("native_publish_failed", "upload failed"),
    )

    assert execute_generation_item(item.id, "celery-1") == SDKGenerationStatusEnum.PARTIAL.value
    assert item.artifacts.filter(filename="manifest.json", status=SDKGenerationStatusEnum.SUCCESS.value).exists()

    publish.side_effect = None
    publish.return_value = []
    assert execute_generation_item(item.id, "celery-2") == SDKGenerationStatusEnum.SUCCESS.value
    assert build.call_count == 1


def test_failed_pre_manifest_upload_can_retry_changed_artifact(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    build, _ = _patch_pipeline(mocker, bkrepo)
    original_upload = bkrepo.upload_generic_file
    manifest_attempts = 0

    def fail_first_manifest(filepath, key, allow_overwrite=True):
        nonlocal manifest_attempts
        if key.endswith("/manifest.json") and manifest_attempts == 0:
            manifest_attempts += 1
            raise RuntimeError("manifest upload failed")
        return original_upload(filepath, key, allow_overwrite)

    bkrepo.upload_generic_file = fail_first_manifest

    assert execute_generation_item(item.id, "celery-1") == SDKGenerationStatusEnum.FAILED.value

    def build_changed(_language, _source, output, _config):
        output.mkdir(parents=True, exist_ok=True)
        path = output / "demo.whl"
        path.write_bytes(b"changed-wheel")
        return [create_built_artifact("wheel", path, allowed_roots=(output,))]

    build.side_effect = build_changed

    assert execute_generation_item(item.id, "celery-2") == SDKGenerationStatusEnum.SUCCESS.value
    artifact = item.artifacts.get(filename="demo.whl")
    assert bkrepo.files[artifact.remote_key] == b"changed-wheel"


def test_execute_stops_after_lease_is_stolen(fake_resource_version, mocker, caplog):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    build, publish = _patch_pipeline(mocker, bkrepo)

    def steal_lease(*_args):
        type(item).objects.filter(id=item.id).update(lease_token="stolen")

    mocker.patch("apigateway.biz.sdk.orchestrator.generate_client", side_effect=steal_lease)
    record_result = mocker.patch("apigateway.biz.sdk.metrics.SDKGenerationMetrics.record_result")

    with caplog.at_level(logging.WARNING):
        assert execute_generation_item(item.id, "celery-1") == SDKGenerationStatusEnum.RUNNING.value

    build.assert_not_called()
    publish.assert_not_called()
    record_result.assert_called_once_with("python", "lease_lost")
    assert "lease" in caplog.text.lower()


def test_retry_enqueues_only_failed_partial_and_expired(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python", "go", "rust"], "admin")
    python = task.items.get(language="python")
    go = task.items.get(language="go")
    rust = task.items.get(language="rust")
    python.status = SDKGenerationStatusEnum.FAILED.value
    python.save(update_fields=["status"])
    go.status = SDKGenerationStatusEnum.SUCCESS.value
    go.save(update_fields=["status"])
    rust.status = SDKGenerationStatusEnum.RUNNING.value
    rust.lease_expires_at = timezone.now() - timedelta(seconds=1)
    rust.save(update_fields=["status", "lease_expires_at"])
    refresh_task_status(task.id)
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        retry_generation_task(task, enqueue)

    enqueue.assert_called_once_with([python.id, rust.id])
    assert set(task.items.filter(id__in=[python.id, rust.id]).values_list("status", flat=True)) == {
        SDKGenerationStatusEnum.PENDING.value
    }
    task.refresh_from_db()
    assert task.status == SDKGenerationStatusEnum.PENDING.value
