from datetime import timedelta

import pytest
from django.utils import timezone

from apigateway.apps.support.constants import SDKGenerationItemStatusEnum
from apigateway.apps.support.models import SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk.orchestrator import (
    ItemExecutionResult,
    claim_generation_item,
    create_or_resume_generation,
    execute_generation_item,
    finish_generation_item,
)
from apigateway.biz.sdk.storage import delete_incomplete_artifacts as guarded_delete_incomplete_artifacts
from apigateway.biz.sdk.tasks import (
    cleanup_incomplete_sdk_artifacts,
    enqueue_generation_items,
    generate_sdk_item,
    publish_sdk_item_native,
    recover_stale_sdk_generation_items,
)
from apigateway.conf.celery_conf import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES

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
    settings.SDK_GENERATION_ENABLED = True


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
    assert CELERY_TASK_ROUTES[generate_sdk_item.name]["queue"] == "sdk.generate"
    assert publish_sdk_item_native.acks_late is True
    assert publish_sdk_item_native.reject_on_worker_lost is True
    assert CELERY_TASK_ROUTES[publish_sdk_item_native.name]["queue"] == "sdk.generate"
    assert CELERY_BEAT_SCHEDULE["recover_stale_sdk_generation_items"]["task"] == (
        "apigateway.biz.sdk.tasks.recover_stale_sdk_generation_items"
    )


def test_generate_sdk_item_uses_celery_request_id(mocker):
    execute = mocker.patch(
        "apigateway.biz.sdk.tasks.execute_generation_item",
        return_value=ItemExecutionResult(status="success", retry_delay_seconds=None),
    )
    task = generate_sdk_item
    task.request.id = "celery-task-id"

    assert task.run(42) == "success"
    execute.assert_called_once_with(42, "celery-task-id")


def test_generate_sdk_item_schedules_explicit_retry(mocker):
    mocker.patch(
        "apigateway.biz.sdk.tasks.execute_generation_item",
        return_value=ItemExecutionResult(status="pending", retry_delay_seconds=30),
    )
    apply_async = mocker.patch.object(generate_sdk_item, "apply_async")
    generate_sdk_item.request.id = "celery-task-id"

    assert generate_sdk_item.run(42) == "pending"
    apply_async.assert_called_once_with(args=(42,), countdown=30, queue="sdk.custom")


def test_generate_sdk_item_enqueues_pending_native_publication(fake_resource_version, settings, mocker):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(status="success")
    mocker.patch(
        "apigateway.biz.sdk.tasks.execute_generation_item",
        return_value=ItemExecutionResult(status="success", retry_delay_seconds=None),
    )
    publish = mocker.patch.object(publish_sdk_item_native, "apply_async")
    generate_sdk_item.request.id = "celery-task-id"

    assert generate_sdk_item.run(item.id) == "success"
    publish.assert_called_once_with(args=(item.id,), queue="sdk.custom")


def test_native_task_schedules_explicit_retry(mocker):
    mocker.patch(
        "apigateway.biz.sdk.tasks.execute_native_publication",
        return_value=ItemExecutionResult(status="pending", retry_delay_seconds=120),
    )
    apply_async = mocker.patch.object(publish_sdk_item_native, "apply_async")
    publish_sdk_item_native.request.id = "celery-native"

    assert publish_sdk_item_native.run(42) == "pending"
    apply_async.assert_called_once_with(args=(42,), countdown=120, queue="sdk.custom")


def test_disabled_worker_does_not_claim_pending_item(fake_resource_version, settings):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    settings.SDK_GENERATION_ENABLED = False

    assert execute_generation_item(item.id, "disabled-worker") is None

    item.refresh_from_db()
    assert item.status == "pending"
    assert item.attempt_count == 0


def test_leased_item_can_finish_after_feature_is_disabled(fake_resource_version, settings):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    claim = claim_generation_item(item.id, "active-worker")
    assert claim is not None
    settings.SDK_GENERATION_ENABLED = False

    assert finish_generation_item(claim, "success") is True

    item.refresh_from_db()
    assert item.status == "success"


def test_recover_stale_items_clears_lease_and_requeues(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    expired = task.items.get(language="python")
    active = task.items.get(language="go")
    expired.status = SDKGenerationItemStatusEnum.RUNNING.value
    expired.lease_token = "expired"
    expired.lease_expires_at = timezone.now() - timedelta(seconds=1)
    expired.save(update_fields=["status", "lease_token", "lease_expires_at"])
    active.status = SDKGenerationItemStatusEnum.RUNNING.value
    active.lease_token = "active"
    active.lease_expires_at = timezone.now() + timedelta(minutes=5)
    active.save(update_fields=["status", "lease_token", "lease_expires_at"])
    enqueue = mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")

    with django_capture_on_commit_callbacks(execute=True):
        assert recover_stale_sdk_generation_items() == 1

    expired.refresh_from_db()
    active.refresh_from_db()
    assert expired.status == SDKGenerationItemStatusEnum.PENDING.value
    assert expired.lease_token == ""
    assert expired.lease_expires_at is None
    assert active.status == SDKGenerationItemStatusEnum.RUNNING.value
    enqueue.assert_called_once_with([expired.id])


def test_recovery_locks_tasks_before_generation_items(fake_resource_version, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(
        status=SDKGenerationItemStatusEnum.RUNNING.value,
        lease_token="expired",
        lease_expires_at=timezone.now() - timedelta(seconds=1),
    )
    lock_order = []
    lock_task = SDKGenerationTask.objects.select_for_update
    lock_item = SDKGenerationItem.objects.select_for_update
    mocker.patch.object(
        SDKGenerationTask.objects,
        "select_for_update",
        side_effect=lambda *args, **kwargs: (lock_order.append("task"), lock_task(*args, **kwargs))[1],
    )
    mocker.patch.object(
        SDKGenerationItem.objects,
        "select_for_update",
        side_effect=lambda *args, **kwargs: (lock_order.append("item"), lock_item(*args, **kwargs))[1],
    )
    mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")

    recover_stale_sdk_generation_items()

    assert lock_order[:2] == ["task", "item"]


def test_recover_stale_pending_item_when_initial_enqueue_was_lost(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python", "go"], "admin")
    stale = task.items.get(language="python")
    recent = task.items.get(language="go")
    task.items.filter(id=stale.id).update(updated_time=timezone.now() - timedelta(minutes=10))
    enqueue = mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")

    with django_capture_on_commit_callbacks(execute=True):
        assert recover_stale_sdk_generation_items() == 1

    enqueue.assert_called_once_with([stale.id])
    recent.refresh_from_db()
    assert recent.status == SDKGenerationItemStatusEnum.PENDING.value


def test_recover_dispatches_due_retry_without_waiting_for_stale_cutoff(
    fake_resource_version, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    enqueue = mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")

    with django_capture_on_commit_callbacks(execute=True):
        assert recover_stale_sdk_generation_items() == 1

    enqueue.assert_called_once_with([item.id])


def test_recover_dispatches_due_native_publication(
    fake_resource_version, settings, mocker, django_capture_on_commit_callbacks
):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/pypi"}}
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(
        status="success",
        native_status="pending",
        native_next_attempt_at=timezone.now() - timedelta(seconds=1),
    )
    enqueue_generation = mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")
    enqueue_native = mocker.patch("apigateway.biz.sdk.tasks.enqueue_native_publications")
    settings.SDK_GENERATION_ENABLED = False

    assert recover_stale_sdk_generation_items() == 0
    enqueue_native.assert_not_called()

    settings.SDK_GENERATION_ENABLED = True
    with django_capture_on_commit_callbacks(execute=True):
        assert recover_stale_sdk_generation_items() == 1

    enqueue_generation.assert_not_called()
    enqueue_native.assert_called_once_with([item.id])


def test_recovery_resumes_stale_pending_item_after_reenable(
    fake_resource_version, settings, mocker, django_capture_on_commit_callbacks
):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    task.items.filter(id=item.id).update(updated_time=timezone.now() - timedelta(minutes=10))
    enqueue = mocker.patch("apigateway.biz.sdk.tasks.enqueue_generation_items")
    settings.SDK_GENERATION_ENABLED = False

    assert recover_stale_sdk_generation_items() == 0
    enqueue.assert_not_called()

    settings.SDK_GENERATION_ENABLED = True
    with django_capture_on_commit_callbacks(execute=True):
        assert recover_stale_sdk_generation_items() == 1
    enqueue.assert_called_once_with([item.id])


def test_cleanup_only_processes_old_failed_or_expired_items(fake_resource_version, settings, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python", "go", "javascript"], "admin")
    failed = task.items.get(language="python")
    expired = task.items.get(language="go")
    recent = task.items.get(language="javascript")
    old = timezone.now() - timedelta(hours=settings.SDK_GENERATION["generic_retention_hours"] + 1)
    task.items.filter(id=failed.id).update(
        status=SDKGenerationItemStatusEnum.FAILED.value, input_fingerprint="a" * 64, updated_time=old
    )
    task.items.filter(id=expired.id).update(
        status=SDKGenerationItemStatusEnum.RUNNING.value,
        input_fingerprint="b" * 64,
        lease_expires_at=timezone.now() - timedelta(seconds=1),
        updated_time=old,
    )
    task.items.filter(id=recent.id).update(status=SDKGenerationItemStatusEnum.FAILED.value, input_fingerprint="c" * 64)
    bkrepo = mocker.Mock()
    mocker.patch("apigateway.biz.sdk.tasks.BKRepoComponent.default", return_value=bkrepo)
    delete = mocker.patch("apigateway.biz.sdk.tasks.delete_incomplete_artifacts", side_effect=[2, 3])

    assert cleanup_incomplete_sdk_artifacts() == 5
    assert {call.args[0].id for call in delete.call_args_list} == {failed.id, expired.id}


def test_cleanup_rechecks_item_state_before_deleting(fake_resource_version, settings, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    old = timezone.now() - timedelta(hours=settings.SDK_GENERATION["generic_retention_hours"] + 1)
    task.items.filter(id=item.id).update(
        status=SDKGenerationItemStatusEnum.FAILED.value,
        input_fingerprint="a" * 64,
        updated_time=old,
    )
    mocker.patch("apigateway.biz.sdk.tasks.BKRepoComponent.default", return_value=mocker.Mock())

    def activate_retry(candidate, bkrepo, **kwargs):
        task.items.filter(id=candidate.id).update(
            status=SDKGenerationItemStatusEnum.RUNNING.value,
            lease_token="new-worker",
            lease_expires_at=timezone.now() + timedelta(minutes=5),
            updated_time=timezone.now(),
        )
        return guarded_delete_incomplete_artifacts(candidate, bkrepo, **kwargs)

    delete = mocker.patch("apigateway.biz.sdk.tasks.delete_incomplete_artifacts", side_effect=activate_retry)

    assert cleanup_incomplete_sdk_artifacts() == 0
    delete.assert_called_once()


def test_cleanup_rechecks_fingerprint_before_deleting(fake_resource_version, settings, mocker):
    task = create_or_resume_generation(fake_resource_version, ["python"], "admin")
    item = task.items.get()
    old = timezone.now() - timedelta(hours=settings.SDK_GENERATION["generic_retention_hours"] + 1)
    task.items.filter(id=item.id).update(
        status=SDKGenerationItemStatusEnum.FAILED.value,
        input_fingerprint="a" * 64,
        updated_time=old,
    )
    mocker.patch("apigateway.biz.sdk.tasks.BKRepoComponent.default", return_value=mocker.Mock())

    def replace_fingerprint(candidate, bkrepo, **kwargs):
        task.items.filter(id=candidate.id).update(input_fingerprint="b" * 64)
        return guarded_delete_incomplete_artifacts(candidate, bkrepo, **kwargs)

    mocker.patch("apigateway.biz.sdk.tasks.delete_incomplete_artifacts", side_effect=replace_fingerprint)

    assert cleanup_incomplete_sdk_artifacts() == 0
