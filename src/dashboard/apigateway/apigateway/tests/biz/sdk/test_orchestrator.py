from datetime import timedelta
from pathlib import Path

import pytest
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
        self.files[key] = Path(filepath).read_bytes()

    def download_generic_file(self, key, filepath):
        Path(filepath).write_bytes(self.files[key])
        return Path(filepath)

    def get_generic_file_metadata(self, key):
        return {} if key in self.files else None

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


def test_create_skips_success_and_unexpired_running_items(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    python = task.items.get(language="python")
    python.status = SDKGenerationStatusEnum.SUCCESS.value
    python.save(update_fields=["status"])
    go = task.items.get(language="go")
    go.status = SDKGenerationStatusEnum.RUNNING.value
    go.lease_expires_at = timezone.now() + timedelta(minutes=5)
    go.save(update_fields=["status", "lease_expires_at"])
    enqueue = mocker.Mock()

    create_or_resume_generation(fake_resource_version, ["python", "go"], "admin", enqueue)

    enqueue.assert_not_called()


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
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        retry_generation_task(task, enqueue)

    enqueue.assert_called_once_with([python.id, rust.id])
