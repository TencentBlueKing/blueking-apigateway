#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import redis_lock
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.gateway import build_gateway_authorization, get_gateway_iam_system_operator
from apigateway.components.bkiam import MAX_BATCH_SIZE, add_authorization
from apigateway.core.models import Gateway
from apigateway.utils.redis_utils import get_default_redis_client

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = logging.getLogger(__name__)

RENEWAL_WINDOW_DAYS = 30
AUTHORIZATION_EXPIRE_DAYS = 365
RENEWAL_LOCK_NAME = "renew_gateway_member_iam_authorizations"


def _chunks(members: list[GatewayMember]) -> Iterable[list[GatewayMember]]:
    for offset in range(0, len(members), MAX_BATCH_SIZE):
        yield members[offset : offset + MAX_BATCH_SIZE]


def _due_members(gateway_id: int, due_before: datetime) -> list[GatewayMember]:
    return list(
        GatewayMember.objects.filter(gateway_id=gateway_id)
        .filter(Q(expires__isnull=True) | Q(expires__lte=due_before))
        .order_by("username", "id")
    )


@transaction.atomic
def _renew_gateway_member_iam_authorizations(
    gateway_id: int,
    due_before: datetime,
    renewed_expires: datetime,
) -> int:
    # Member writes use this same gateway row lock, so role changes and deletes
    # cannot race the snapshot sent to IAM.
    gateway = Gateway.objects.select_for_update().filter(id=gateway_id).first()
    if gateway is None:
        return 0

    operator = get_gateway_iam_system_operator()
    members = _due_members(gateway.id, due_before)
    failed_batches = 0
    for batch_members in _chunks(members):
        member_ids = [member.id for member in batch_members]
        authorizations = [
            build_gateway_authorization(
                member.username,
                member.role,
                gateway.id,
                renewed_expires,
            )
            for member in batch_members
        ]
        try:
            add_authorization(authorizations, operator)
        except Exception:
            failed_batches += 1
            logger.exception(
                "failed to renew gateway member IAM authorizations, gateway_id=%d, member_ids=%s",
                gateway.id,
                member_ids,
            )
            continue

        GatewayMember.objects.filter(id__in=member_ids).update(expires=renewed_expires)

    return failed_batches


@shared_task(
    name="apigateway.apps.rbac.tasks.renew_gateway_member_iam_authorizations",
    ignore_result=True,
)
def renew_gateway_member_iam_authorizations() -> None:
    """Renew IAM authorizations that expire within 30 days."""
    if not settings.BK_IAM_V4_ENABLED:
        return

    lock = redis_lock.Lock(
        get_default_redis_client(),
        RENEWAL_LOCK_NAME,
        expire=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
        auto_renewal=True,
        strict=False,
    )
    if not lock.acquire(blocking=False):
        logger.info("skip gateway member IAM authorization renewal because the task lock is held")
        return

    try:
        now = timezone.now()
        due_before = now + timedelta(days=RENEWAL_WINDOW_DAYS)
        renewed_expires = now + timedelta(days=AUTHORIZATION_EXPIRE_DAYS)
        gateway_ids = list(
            GatewayMember.objects.filter(Q(expires__isnull=True) | Q(expires__lte=due_before))
            .order_by("gateway_id")
            .values_list("gateway_id", flat=True)
            .distinct()
        )

        failed_batches = 0
        for gateway_id in gateway_ids:
            try:
                failed_batches += _renew_gateway_member_iam_authorizations(
                    gateway_id,
                    due_before,
                    renewed_expires,
                )
            except Exception:
                failed_batches += 1
                logger.exception(
                    "failed to process gateway member IAM authorization renewal, gateway_id=%d",
                    gateway_id,
                )

        if failed_batches:
            raise RuntimeError(f"failed to renew {failed_batches} gateway member IAM authorization batches")
    finally:
        try:
            lock.release()
        except Exception:
            logger.exception("failed to release gateway member IAM authorization renewal lock")
