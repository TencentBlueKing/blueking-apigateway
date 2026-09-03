import logging
from datetime import timedelta
from pathlib import Path

import pytest
import requests
from blue_krill.storages.blobstore.exceptions import ObjectAlreadyExists, RequestError, UploadFailedError
from ddf import G
from django.utils import timezone

from apigateway.apps.support.constants import (
    SDKDistributorEnum,
    SDKGenerationItemStatusEnum,
    SDKGenerationTaskStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.sdk.artifacts import create_built_artifact
from apigateway.biz.sdk.exceptions import SDKGenerationError
from apigateway.biz.sdk.orchestrator import (
    GenerationClaim,
    NativePublicationClaim,
    _classify_generation_error,
    claim_generation_item,
    claim_native_publication,
    create_or_resume_generation,
    execute_generation_item,
    execute_native_publication,
    finish_generation_item,
    finish_native_publication,
    refresh_task_status,
    serialize_generation_task,
)
from apigateway.biz.sdk.toolchain import SDKToolchainIdentity

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
    settings.SDK_GENERATION_ENABLED = True
    settings.SDK_GENERATION_RETRY_DELAYS = (30, 120)


def test_create_deduplicates_languages_and_enqueues_on_commit(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        task = create_or_resume_generation(fake_resource_version, ["python", "go", "python"], "admin", enqueue)

    assert list(task.items.values_list("language", flat=True).order_by("id")) == ["python", "go"]
    enqueue.assert_called_once_with(list(task.items.values_list("id", flat=True).order_by("id")))


def test_create_assigns_native_status_only_for_enabled_python_and_java_repositories(fake_resource_version, settings):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    settings.MAVEN_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/maven"}}

    task = create_or_resume_generation(fake_resource_version, ["python", "java", "go", "javascript"], "admin")

    statuses = dict(task.items.values_list("language", "native_status"))
    assert statuses == {
        "python": "pending",
        "java": "pending",
        "go": "not_required",
        "javascript": "not_required",
    }


def test_create_reuses_task_and_keeps_active_item_when_adding_language(fake_resource_version):
    first_task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    first_item = first_task.items.get()
    first_item.status = SDKGenerationItemStatusEnum.RUNNING.value
    first_item.lease_token = "active"
    first_item.lease_expires_at = timezone.now() + timedelta(minutes=5)
    first_item.config_snapshot = {"request": "first"}
    first_item.save(update_fields=["status", "lease_token", "lease_expires_at", "config_snapshot"])

    second_task = create_or_resume_generation(fake_resource_version, ["go"], "admin")

    first_item.refresh_from_db()
    assert second_task.id == first_task.id
    assert set(second_task.items.values_list("language", flat=True)) == {"python", "go"}
    assert first_item.status == SDKGenerationItemStatusEnum.RUNNING.value
    assert first_item.lease_token == "active"
    assert first_item.config_snapshot == {"request": "first"}


def test_create_reuses_success_item_and_only_enqueues_missing_language(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    python = task.items.get()
    task.items.filter(id=python.id).update(status="success")
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        repeated = create_or_resume_generation(fake_resource_version, ["python", "javascript"], "admin", enqueue)

    assert repeated.id == task.id
    assert repeated.items.get(language="python").id == python.id
    enqueue.assert_called_once_with([repeated.items.get(language="javascript").id])


def test_create_resumes_failed_transient_item_on_same_row(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(
        status="failed",
        error_code="temporary_network",
        error_retryable=True,
        attempt_count=3,
        attempt_cycle_count=3,
    )
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        repeated = create_or_resume_generation(fake_resource_version, ["python"], "admin", enqueue)

    resumed = repeated.items.get()
    assert resumed.id == item.id
    assert resumed.status == "pending"
    assert resumed.attempt_count == 3
    assert resumed.attempt_cycle_count == 0
    enqueue.assert_called_once_with([item.id])


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


def test_claim_obeys_retry_due_time_and_counts_attempt_cycle(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    item.next_attempt_at = timezone.now() + timedelta(minutes=1)
    item.save(update_fields=["next_attempt_at"])

    assert claim_generation_item(item.id, "too-early") is None

    item.next_attempt_at = timezone.now() - timedelta(seconds=1)
    item.save(update_fields=["next_attempt_at"])
    assert claim_generation_item(item.id, "due") is not None
    item.refresh_from_db()
    assert item.attempt_count == 1
    assert item.attempt_cycle_count == 1


def test_finish_rejects_wrong_lease_token(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    claim = claim_generation_item(item.id, "owner")
    assert claim is not None

    assert finish_generation_item(GenerationClaim(item.id, "wrong"), "success") is False

    item.refresh_from_db()
    assert item.status == "running"


def test_claim_marks_parent_task_running(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()

    assert claim_generation_item(item.id, "celery-1") is not None

    task.refresh_from_db()
    assert task.status == SDKGenerationTaskStatusEnum.RUNNING.value


def test_refresh_reports_running_when_successful_task_adds_pending_language(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    task.items.filter(language="python").update(status=SDKGenerationItemStatusEnum.SUCCESS.value)

    assert refresh_task_status(task.id) == SDKGenerationTaskStatusEnum.RUNNING.value


def test_refresh_and_serialization_report_partial_task(fake_resource_version):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    task.items.filter(language="python").update(status=SDKGenerationItemStatusEnum.SUCCESS.value)
    task.items.filter(language="go").update(
        status=SDKGenerationItemStatusEnum.FAILED.value, error_code="build_failed", error_message="failed"
    )

    assert refresh_task_status(task.id) == SDKGenerationTaskStatusEnum.PARTIAL.value
    task.refresh_from_db()
    payload = serialize_generation_task(task)
    assert payload["status"] == "partial"
    assert payload["items"][1]["error"] == {"code": "build_failed", "message": "failed"}


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["pending"], "pending"),
        (["running"], "running"),
        (["pending", "success"], "running"),
        (["success"], "success"),
        (["failed"], "failed"),
        (["success", "failed"], "partial"),
    ],
)
def test_refresh_task_status_precedence(fake_resource_version, statuses, expected):
    languages = ["python", "java"][: len(statuses)]
    task = create_or_resume_generation(fake_resource_version, languages, "admin")
    for item, status in zip(task.items.order_by("id"), statuses, strict=True):
        item.status = status
        item.save(update_fields=["status"])

    assert refresh_task_status(task.id) == expected


def test_legacy_sdk_is_linked_as_success_without_enqueue_or_update(
    fake_gateway, fake_resource_version, mocker, django_capture_on_commit_callbacks
):
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

    original = (sdk.name, sdk.url, sdk._config, sdk.updated_time)
    enqueue = mocker.Mock()

    with django_capture_on_commit_callbacks(execute=True):
        task = create_or_resume_generation(fake_resource_version, ["python"], "admin", enqueue)

    item = task.items.get()
    sdk.refresh_from_db()
    assert item.gateway_sdk == sdk
    assert item.status == "success"
    assert not item.artifacts.exists()
    assert (sdk.name, sdk.url, sdk._config, sdk.updated_time) == original
    enqueue.assert_not_called()


def _patch_pipeline(mocker, bkrepo, *, publisher_side_effect=None):
    mocker.patch("apigateway.biz.sdk.orchestrator.BKRepoComponent.default", return_value=bkrepo)
    mocker.patch(
        "apigateway.biz.sdk.orchestrator.probe_toolchain_identity",
        return_value=SDKToolchainIdentity(
            openapi_generator="7.23.0",
            python="3.14.5",
            java="17.0.15",
            maven="3.9.9",
            go="1.24.4",
            node="22.17.0",
            npm="10.9.2",
            dependency_lock_sha256="a" * 64,
        ),
    )
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
    _, publish = _patch_pipeline(mocker, bkrepo)

    result = execute_generation_item(item.id, "celery-1")
    assert result is not None
    assert result.status == SDKGenerationItemStatusEnum.SUCCESS.value
    assert result.retry_delay_seconds is None

    item.refresh_from_db()
    assert item.artifacts.filter(
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        filename="manifest.json",
        status=SDKGenerationItemStatusEnum.SUCCESS.value,
    ).exists()
    sdk = GatewaySDK.objects.get(gateway=fake_gateway, language="python", version_number=fake_resource_version.version)
    assert sdk.config == {}
    assert sdk.generation_item.id == item.id
    publish.assert_not_called()


def test_execute_fingerprints_the_complete_worker_identity(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _patch_pipeline(mocker, bkrepo)
    identity = SDKToolchainIdentity(
        openapi_generator="7.23.0",
        python="3.14.5",
        java="17.0.15",
        maven="3.9.9",
        go="1.24.4",
        node="22.17.0",
        npm="10.9.2",
        dependency_lock_sha256="a" * 64,
    )
    mocker.patch("apigateway.biz.sdk.orchestrator.probe_toolchain_identity", return_value=identity)
    calculate = mocker.patch(
        "apigateway.biz.sdk.orchestrator.calculate_input_fingerprint",
        return_value="b" * 64,
    )

    result = execute_generation_item(item.id, "celery-identity")

    assert result is not None and result.status == SDKGenerationItemStatusEnum.SUCCESS.value
    assert calculate.call_args.args[2] == identity


def test_generic_success_is_committed_before_native_publication(fake_resource_version, settings, mocker):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _, publish = _patch_pipeline(mocker, bkrepo)

    result = execute_generation_item(item.id, "celery-generation")

    assert result is not None and result.status == "success"
    item.refresh_from_db()
    task.refresh_from_db()
    assert item.status == "success"
    assert item.native_status == "pending"
    assert task.status == "success"
    publish.assert_not_called()


def test_native_publication_restores_generic_artifacts_and_keeps_generation_success(
    fake_resource_version, settings, mocker
):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    build, publish = _patch_pipeline(mocker, bkrepo)
    assert execute_generation_item(item.id, "celery-generation").status == "success"
    publish.return_value = []

    result = execute_native_publication(item.id, "celery-native")

    assert result is not None and result.status == "success"
    item.refresh_from_db()
    task.refresh_from_db()
    assert item.status == "success"
    assert item.native_status == "success"
    assert task.status == "success"
    assert build.call_count == 1
    assert publish.call_count == 1
    assert publish.call_args.args[1][0].artifact_type == "wheel"


def test_native_lease_owner_is_enforced(fake_resource_version, settings):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(status="success")

    claim = claim_native_publication(item.id, "native-owner")

    assert claim is not None
    assert claim_native_publication(item.id, "other-owner") is None
    assert finish_native_publication(NativePublicationClaim(item.id, "wrong"), "success") is False


def test_disabled_worker_leaves_native_pending_and_claimed_work_can_finish(fake_resource_version, settings):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(status="success")
    settings.SDK_GENERATION_ENABLED = False

    assert claim_native_publication(item.id, "disabled") is None
    item.refresh_from_db()
    assert item.native_status == "pending"
    assert item.native_attempt_count == 0

    settings.SDK_GENERATION_ENABLED = True
    claim = claim_native_publication(item.id, "active")
    assert claim is not None
    settings.SDK_GENERATION_ENABLED = False
    assert finish_native_publication(claim, "success") is True


def test_deterministic_native_failure_does_not_downgrade_generation(fake_resource_version, settings, mocker):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _, publish = _patch_pipeline(mocker, bkrepo)
    assert execute_generation_item(item.id, "celery-generation").status == "success"
    publish.side_effect = SDKGenerationError("registry_authentication", "unauthorized")

    result = execute_native_publication(item.id, "celery-native")

    assert result is not None and result.status == "failed"
    assert result.retry_delay_seconds is None
    item.refresh_from_db()
    task.refresh_from_db()
    assert item.status == "success"
    assert item.native_status == "failed"
    assert task.status == "success"


def test_native_transient_retries_then_fails_without_downgrading_generation(fake_resource_version, settings, mocker):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _, publish = _patch_pipeline(mocker, bkrepo)
    assert execute_generation_item(item.id, "celery-generation").status == "success"
    publish.side_effect = SDKGenerationError("temporary_network", "temporary", retryable=True)

    countdowns = []
    for attempt in range(3):
        if attempt:
            task.items.filter(id=item.id).update(native_next_attempt_at=timezone.now() - timedelta(seconds=1))
        result = execute_native_publication(item.id, f"celery-native-{attempt}")
        assert result is not None
        if result.retry_delay_seconds is not None:
            countdowns.append(result.retry_delay_seconds)

    item.refresh_from_db()
    task.refresh_from_db()
    assert countdowns == [30, 120]
    assert item.status == "success"
    assert item.native_status == "failed"
    assert item.native_attempt_count == 3
    assert item.native_attempt_cycle_count == 3
    assert task.status == "success"


def test_transient_failure_retries_at_30_then_120_and_third_failure_is_terminal(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _patch_pipeline(mocker, bkrepo)
    mocker.patch(
        "apigateway.biz.sdk.orchestrator.generate_client",
        side_effect=SDKGenerationError("temporary_network", "temporary failure", retryable=True),
    )

    countdowns = []
    for attempt in range(3):
        if attempt:
            item.refresh_from_db()
            item.next_attempt_at = timezone.now() - timedelta(seconds=1)
            item.save(update_fields=["next_attempt_at"])
        result = execute_generation_item(item.id, f"celery-{attempt}")
        assert result is not None
        if result.retry_delay_seconds is not None:
            countdowns.append(result.retry_delay_seconds)

    item.refresh_from_db()
    assert countdowns == [30, 120]
    assert item.attempt_count == 3
    assert item.attempt_cycle_count == 3
    assert item.status == "failed"


def test_deterministic_failure_is_terminal_immediately(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    bkrepo = FakeBKRepo()
    _patch_pipeline(mocker, bkrepo)
    mocker.patch(
        "apigateway.biz.sdk.orchestrator.generate_client",
        side_effect=SDKGenerationError("generator_validation", "invalid input"),
    )

    result = execute_generation_item(item.id, "celery-1")

    assert result is not None
    assert result.status == "failed"
    assert result.retry_delay_seconds is None
    item.refresh_from_db()
    assert item.attempt_count == 1
    assert item.attempt_cycle_count == 1


@pytest.mark.parametrize(("status_code", "retryable"), [(429, True), (503, True), (401, False)])
def test_remote_http_error_classification(status_code, retryable):
    response = requests.Response()
    response.status_code = status_code
    error = requests.HTTPError(response=response)

    classified = _classify_generation_error(error)

    assert classified.retryable is retryable


@pytest.mark.parametrize(("status_code", "retryable"), [("429", True), ("503", True), ("401", False)])
@pytest.mark.parametrize("wrapped", [False, True])
def test_bkrepo_error_classification_follows_wrapped_http_status(status_code, retryable, wrapped):
    response = requests.Response()
    response.status_code = int(status_code)
    request_error = RequestError("BKRepo request failed", code=status_code, response=response)
    error = UploadFailedError("artifact.whl", "/tmp/artifact.whl") if wrapped else request_error
    if wrapped:
        error.__cause__ = request_error

    classified = _classify_generation_error(error)

    assert classified.retryable is retryable
    assert classified.code == ("remote_service_unavailable" if retryable else "remote_request_failed")


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

    first = execute_generation_item(item.id, "celery-1")
    assert first is not None
    assert first.status == SDKGenerationItemStatusEnum.FAILED.value

    def build_changed(_language, _source, output, _config):
        output.mkdir(parents=True, exist_ok=True)
        path = output / "demo.whl"
        path.write_bytes(b"changed-wheel")
        return [create_built_artifact("wheel", path, allowed_roots=(output,))]

    build.side_effect = build_changed

    task.items.filter(id=item.id).update(status="pending", attempt_cycle_count=0)
    second = execute_generation_item(item.id, "celery-2")
    assert second is not None
    assert second.status == SDKGenerationItemStatusEnum.SUCCESS.value
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
        result = execute_generation_item(item.id, "celery-1")
        assert result is not None
        assert result.status == SDKGenerationItemStatusEnum.RUNNING.value

    build.assert_not_called()
    publish.assert_not_called()
    record_result.assert_called_once_with("python", "failed", "lease_lost")
    assert "lease" in caplog.text.lower()
