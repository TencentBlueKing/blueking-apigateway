# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import base64
import logging
import os
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Set, Tuple

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apigateway.apps.metrics.models import StatisticsGatewayRequestByDay
from apigateway.biz.gateway.gateway import OPERATION_STATUS_DELTA_DAYS, GatewayHandler
from apigateway.common.tenant.constants import TENANT_MODE_SINGLE_DEFAULT_TENANT_ID
from apigateway.components.bkcmsi import cmsi_component
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release
from apigateway.utils.file import read_file

logger = logging.getLogger(__name__)

APIGW_LOGO_PATH = os.path.join(settings.BASE_DIR, "static/img/api_gateway.png")


@shared_task(name="apigateway.apps.gateway.tasks.notify_inactive_gateway_maintainers", ignore_result=True)
def notify_inactive_gateway_maintainers():
    """每月 1 号通知网关负责人处理不活跃网关
    note: only enable the task when not in multi-tenant mode
    """
    if not settings.ENABLE_GATEWAY_OPERATION_STATUS or settings.ENABLE_MULTI_TENANT_MODE:
        logger.info(
            "SKIP notify_inactive_gateway_maintainers: ENABLE_GATEWAY_OPERATION_STATUS is disabled or multi-tenant mode is enabled"
        )
        return

    notifier = InactiveGatewayNotifier()
    notifier.notify()


class InactiveGatewayNotifier:
    def notify(self):
        inactive_gateways = self._get_inactive_gateways()
        if not inactive_gateways:
            logger.info("no inactive gateways found, skip sending notification")
            return

        inactive_gateway_ids = [gw.id for gw in inactive_gateways]
        resource_counts = GatewayHandler.get_resource_count(inactive_gateway_ids)
        stage_names_map = self._get_released_stage_names(inactive_gateway_ids)

        gateway_data_map: Dict[int, dict] = {}
        for gw in inactive_gateways:
            gateway_data_map[gw.id] = {
                "name": gw.name,
                "created_by": gw.created_by or "",
                "stage_names": ", ".join(sorted(stage_names_map.get(gw.id, []))),
                "resource_count": resource_counts.get(gw.id, 0),
                "request_count": 0,
            }

        user_to_gateway_ids = self._group_by_user(inactive_gateways)
        mail_groups = self._dedupe_by_gateway_set(user_to_gateway_ids)
        self._send_mails(mail_groups, gateway_data_map, inactive_gateways)

    def _get_inactive_gateways(self) -> List[Gateway]:
        """找到不活跃网关：网关 active、有 active 环境、环境已发布、但过去 180 天无流量"""
        released_gateway_ids = set(
            Release.objects.filter(
                gateway__status=GatewayStatusEnum.ACTIVE.value,
                stage__status=StageStatusEnum.ACTIVE.value,
            )
            .values_list("gateway_id", flat=True)
            .distinct()
        )
        if not released_gateway_ids:
            return []

        end_time = timezone.now()
        start_time = end_time - timedelta(days=OPERATION_STATUS_DELTA_DAYS)

        # filter out recently created gateways at DB level
        gateways = list(Gateway.objects.filter(id__in=released_gateway_ids, created_time__lte=start_time))
        if not gateways:
            return []

        to_check_ids = [gw.id for gw in gateways]

        has_traffic_ids = set(
            StatisticsGatewayRequestByDay.objects.filter(
                gateway_id__in=to_check_ids,
                start_time__gte=start_time,
                end_time__lte=end_time,
            )
            .values_list("gateway_id", flat=True)
            .distinct()
        )

        return [gw for gw in gateways if gw.id not in has_traffic_ids]

    def _get_released_stage_names(self, gateway_ids: List[int]) -> Dict[int, List[str]]:
        """获取已发布的 active 环境名称"""
        releases = (
            Release.objects.filter(
                gateway_id__in=gateway_ids,
                gateway__status=GatewayStatusEnum.ACTIVE.value,
                stage__status=StageStatusEnum.ACTIVE.value,
            )
            .select_related("stage")
            .only("gateway_id", "stage__name")
        )
        result: Dict[int, List[str]] = defaultdict(list)
        seen: Set[Tuple[int, str]] = set()
        for rel in releases:
            key = (rel.gateway_id, rel.stage.name)
            if key not in seen:
                seen.add(key)
                result[rel.gateway_id].append(rel.stage.name)
        return result

    @staticmethod
    def _group_by_user(gateways: List[Gateway]) -> Dict[str, Set[int]]:
        user_to_gateway_ids: Dict[str, Set[int]] = defaultdict(set)
        for gw in gateways:
            for user in gw.maintainers:
                user_to_gateway_ids[user].add(gw.id)
        return user_to_gateway_ids

    @staticmethod
    def _dedupe_by_gateway_set(
        user_to_gateway_ids: Dict[str, Set[int]],
    ) -> Dict[frozenset, List[str]]:
        """相同网关集合的用户合并到同一封邮件"""
        gateway_set_to_users: Dict[frozenset, List[str]] = defaultdict(list)
        for user, gw_ids in user_to_gateway_ids.items():
            gateway_set_to_users[frozenset(gw_ids)].append(user)
        return gateway_set_to_users

    def _send_mails(
        self,
        mail_groups: Dict[frozenset, List[str]],
        gateway_data_map: Dict[int, dict],
        all_gateways: List[Gateway],
    ):
        gray_user_list = getattr(settings, "INACTIVE_GATEWAY_NOTIFY_GRAY_USER_LIST", [])
        apigw_domain = getattr(settings, "DASHBOARD_FE_URL", "").rstrip("/")
        gateway_map = {gw.id: gw for gw in all_gateways}

        for gateway_id_set, users in mail_groups.items():
            receivers = [u for u in users if u in gray_user_list] if gray_user_list else users
            if not receivers:
                continue

            gw_data_list = sorted(
                [gateway_data_map[gw_id] for gw_id in gateway_id_set if gw_id in gateway_data_map],
                key=lambda x: x["name"],
            )
            if not gw_data_list:
                continue

            title = "【蓝鲸API网关】你维护的网关存在不活跃网关，请及时处理"
            mail_content = render_to_string(
                "gateway/inactive_gateway_notify_template.html",
                context={
                    "title": title,
                    "gateways": gw_data_list,
                    "dashboard_link": apigw_domain,
                },
            )

            params = {
                "title": title,
                "receiver__username": ";".join(sorted(receivers)),
                "content": mail_content,
                "attachments": [
                    {
                        "filename": "api_gateway.png",
                        "content": base64.b64encode(read_file(APIGW_LOGO_PATH)).decode("utf-8"),
                    }
                ],
            }

            # not support multi-tenant mode, so the tenant id is always "default"
            ok, error_msg = cmsi_component.send_mail(TENANT_MODE_SINGLE_DEFAULT_TENANT_ID, params)
            if not ok:
                logger.error(
                    "send inactive gateway notification failed, users=%s, gateway_count=%d, error_msg=%s",
                    receivers,
                    len(gw_data_list),
                    error_msg,
                )
            else:
                logger.info(
                    "sent inactive gateway notification to users=%s, gateway_count=%d",
                    receivers,
                    len(gw_data_list),
                )
