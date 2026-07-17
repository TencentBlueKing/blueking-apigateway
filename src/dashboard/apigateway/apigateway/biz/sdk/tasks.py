"""Celery entrypoints for the dedicated SDK generation worker."""

from __future__ import annotations

from datetime import timedelta
from functools import partial

from celery import shared_task
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apigateway.apps.support.constants import SDKGenerationStatusEnum
from apigateway.apps.support.models import SDKGenerationItem
from apigateway.biz.sdk.config import get_sdk_generation_config
from apigateway.biz.sdk.metrics import sdk_generation_metrics
from apigateway.biz.sdk.orchestrator import execute_generation_item, refresh_task_status
from apigateway.biz.sdk.storage import delete_incomplete_artifacts
from apigateway.components.bkrepo import BKRepoComponent


def enqueue_generation_items(item_ids: list[int]) -> None:
    queue = get_sdk_generation_config().queue
    for item_id in item_ids:
        generate_sdk_item.apply_async(args=[item_id], queue=queue)


def _update_item_metrics() -> None:
    counts = dict.fromkeys(SDKGenerationStatusEnum.get_values(), 0)
    counts.update(
        {row["status"]: row["count"] for row in SDKGenerationItem.objects.values("status").annotate(count=Count("id"))}
    )
    sdk_generation_metrics.set_item_counts(counts)


@shared_task(
    bind=True,
    name="apigateway.biz.sdk.tasks.generate_sdk_item",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
)
def generate_sdk_item(self, item_id: int) -> str | None:
    status = execute_generation_item(item_id, self.request.id or "unknown")
    _update_item_metrics()
    return status


@shared_task(name="apigateway.biz.sdk.tasks.recover_stale_sdk_generation_items", ignore_result=True)
def recover_stale_sdk_generation_items() -> int:
    now = timezone.now()
    with transaction.atomic():
        items = list(
            SDKGenerationItem.objects.select_for_update().filter(
                Q(lease_expires_at__lte=now) | Q(lease_expires_at__isnull=True),
                status=SDKGenerationStatusEnum.RUNNING.value,
            )
        )
        if not items:
            _update_item_metrics()
            return 0
        item_ids = [item.id for item in items]
        task_ids = {item.task_id for item in items}
        SDKGenerationItem.objects.filter(id__in=item_ids).update(
            status=SDKGenerationStatusEnum.PENDING.value,
            lease_token="",
            lease_expires_at=None,
            updated_time=now,
        )
        for task_id in task_ids:
            refresh_task_status(task_id)
        transaction.on_commit(partial(enqueue_generation_items, item_ids))
    _update_item_metrics()
    return len(item_ids)


@shared_task(name="apigateway.biz.sdk.tasks.cleanup_incomplete_sdk_artifacts", ignore_result=True)
def cleanup_incomplete_sdk_artifacts() -> int:
    config = get_sdk_generation_config()
    cutoff = timezone.now() - timedelta(hours=config.generic_retention_hours)
    now = timezone.now()
    items = SDKGenerationItem.objects.select_related("task__gateway", "task__resource_version").filter(
        Q(status=SDKGenerationStatusEnum.FAILED.value)
        | Q(status=SDKGenerationStatusEnum.RUNNING.value, lease_expires_at__lte=now),
        input_fingerprint__gt="",
        updated_time__lt=cutoff,
    )
    bkrepo = BKRepoComponent.default()
    if not bkrepo:
        return 0
    deleted = sum(delete_incomplete_artifacts(item, bkrepo) for item in items.iterator())
    _update_item_metrics()
    return deleted
