from datetime import timedelta

import pytest
from django.utils import timezone

from apigateway.apps.support.constants import SDKGenerationStatusEnum
from apigateway.biz.sdk.orchestrator import create_or_resume_generation
from apigateway.biz.sdk.tasks import (
    cleanup_incomplete_sdk_artifacts,
    enqueue_generation_items,
    generate_sdk_item,
    recover_stale_sdk_generation_items,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def sdk_settings(settings, fake_resource_version):
    fake_resource_version.version = "1.2.3"
    fake_resource_version.save(update_fields=["version"])
    settings.BKREPO_ENDPOINT_URL = "https://repo"
    settings.BKREPO_USERNAME = "user"
    settings.BKREPO_PASSWORD = "password"
    settings.BKREPO_PROJECT = "project"
    settings.BKREPO_GENERIC_BUCKET = "generic"
    settings.SDK_GENERATION["queue"] = "sdk.custom"


def test_enqueue_generation_items_routes_every_item_to_sdk_queue(mocker):
    apply_async = mocker.patch.object(generate_sdk_item, "apply_async")

    enqueue_generation_items([11, 12])

    assert apply_async.call_args_list == [
        mocker.call(args=[11], queue="sdk.custom"),
        mocker.call(args=[12], queue="sdk.custom"),
    ]


def test_generate_task_has_worker_loss_delivery_guarantees():
    assert generate_sdk_item.name == "apigateway.biz.sdk.tasks.generate_sdk_item"
    assert generate_sdk_item.acks_late is True
    assert generate_sdk_item.reject_on_worker_lost is True
    assert generate_sdk_item.ignore_result is True


def test_generate_sdk_item_uses_celery_request_id(mocker):
    execute = mocker.patch("apigateway.biz.sdk.tasks.execute_generation_item", return_value="success")
    task = generate_sdk_item
    task.request.id = "celery-task-id"

    assert task.run(42) == "success"
    execute.assert_called_once_with(42, "celery-task-id")


def test_recover_stale_items_clears_lease_and_requeues(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    expired = task.items.get(language="python")
    active = task.items.get(language="go")
    expired.status = SDKGenerationStatusEnum.RUNNING.value
    expired.lease_token = "expired"
    expired.lease_expires_at = timezone.now() - timedelta(seconds=1)
    expired.save(update_fields=["status", "lease_token", "lease_expires_at"])
    active.status = SDKGenerationStatusEnum.RUNNING.value
    active.lease_token = "active"
    active.lease_expires_at = timezone.now() + timedelta(minutes=5)
    active.save(update_fields=["status", "lease_token", "lease_expires_at"])
    enqueue = mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")

    with django_capture_on_commit_callbacks(execute=True):
        assert recover_stale_sdk_generation_items() == 1

    expired.refresh_from_db()
    active.refresh_from_db()
    assert expired.status == SDKGenerationStatusEnum.PENDING.value
    assert expired.lease_token == ""
    assert expired.lease_expires_at is None
    assert active.status == SDKGenerationStatusEnum.RUNNING.value
    enqueue.assert_called_once_with([expired.id])


def test_cleanup_only_processes_old_failed_or_expired_items(fake_resource_version, settings, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python", "go", "rust"], "admin")
    failed = task.items.get(language="python")
    expired = task.items.get(language="go")
    recent = task.items.get(language="rust")
    old = timezone.now() - timedelta(hours=settings.SDK_GENERATION["generic_retention_hours"] + 1)
    task.items.filter(id=failed.id).update(
        status=SDKGenerationStatusEnum.FAILED.value, input_fingerprint="a" * 64, updated_time=old
    )
    task.items.filter(id=expired.id).update(
        status=SDKGenerationStatusEnum.RUNNING.value,
        input_fingerprint="b" * 64,
        lease_expires_at=timezone.now() - timedelta(seconds=1),
        updated_time=old,
    )
    task.items.filter(id=recent.id).update(status=SDKGenerationStatusEnum.FAILED.value, input_fingerprint="c" * 64)
    bkrepo = mocker.Mock()
    mocker.patch("apigateway.biz.sdk.tasks.BKRepoComponent.default", return_value=bkrepo)
    delete = mocker.patch("apigateway.biz.sdk.tasks.delete_incomplete_artifacts", side_effect=[2, 3])

    assert cleanup_incomplete_sdk_artifacts() == 5
    assert {call.args[0].id for call in delete.call_args_list} == {failed.id, expired.id}
