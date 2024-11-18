# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import datetime
import logging
import os
from collections import defaultdict
from typing import Dict, List

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apigateway.apps.metrics.models import StatisticsAppRequestByDay
from apigateway.apps.permission.constants import (
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionRecord,
    AppResourcePermission,
)
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.components.cmsi import cmsi_component
from apigateway.components.paasv3 import paasv3_component
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum, GatewayStatusEnum
from apigateway.core.models import Context, Gateway, Resource
from apigateway.utils.file import read_file

logger = logging.getLogger(__name__)


APIGW_LOGO_PATH = os.path.join(settings.BASE_DIR, "static/img/api_gateway.png")

ONE_DAY_SECONDS = 86400


@shared_task(name="apigateway.apps.permission.tasks.send_mail_for_perm_apply", ignore_result=True)
def send_mail_for_perm_apply(record_id):
    """
    申请权限，发送邮件通知管理员审批
    """
    record = AppPermissionRecord.objects.get(id=record_id)

    apigw_domain = getattr(settings, "DASHBOARD_FE_URL", "").rstrip("/")
    manager = PermissionDimensionManager.get_manager(record.grant_dimension)

    title = f"【蓝鲸API网关】蓝鲸应用【{record.bk_app_code}】访问网关资源权限申请"

    mail_content = render_to_string(
        "permission/perm_apply_mail_template.html",
        context={
            "title": title,
            "api_name": record.gateway.name,
            "bk_app_code": record.bk_app_code,
            "expire_days_display": PermissionApplyExpireDaysEnum.get_choice_label(record.expire_days),
            "grant_dimension_display": GrantDimensionEnum.get_choice_label(record.grant_dimension),
            "resource_names": sorted(manager.get_resource_names_display(record.gateway.id, record.resource_ids)),
            "perm_apply_link": f"{apigw_domain}/{record.gateway_id}/permission/apply",
        },
    )

    params = {
        "title": title,
        "receiver__username": ";".join(record.gateway.maintainers),
        "content": mail_content,
        "attachments": [
            {
                "filename": "api_gateway.png",
                "content": base64.b64encode(read_file(APIGW_LOGO_PATH)).decode("utf-8"),
            }
        ],
    }

    return cmsi_component.send_mail(params)


@shared_task(name="apigateway.apps.permission.tasks.send_mail_for_perm_handle", ignore_result=True)
def send_mail_for_perm_handle(record_id):
    """
    申请单已处理，发送邮件知会申请人
    """
    record = AppPermissionRecord.objects.get(id=record_id)
    handled_resource_ids = record.handled_resource_ids

    manager = PermissionDimensionManager.get_manager(record.grant_dimension)

    approved_resource_names = sorted(
        manager.get_approved_resource_names_display(
            record.gateway.id,
            handled_resource_ids.get(ApplyStatusEnum.APPROVED.value),
            record.status,
        )
    )

    rejected_resource_names = sorted(
        manager.get_rejected_resource_names_display(
            record.gateway.id,
            handled_resource_ids.get(ApplyStatusEnum.REJECTED.value),
            record.status,
        )
    )

    if approved_resource_names:
        part1_permission = {
            "resource_names": approved_resource_names,
            "apply_status": "通过",
            "expire_days_display": PermissionApplyExpireDaysEnum.get_choice_label(record.expire_days),
        }
        part2_permission = {
            "resource_names": rejected_resource_names,
            "apply_status": "驳回",
            "expire_days_display": "0天",
        }
    else:
        part1_permission = {
            "resource_names": rejected_resource_names,
            "apply_status": "驳回",
            "expire_days_display": "0天",
        }
        part2_permission = {}

    title = f"【蓝鲸API网关】你对网关【{record.gateway.name}】资源访问权限的申请已完成"

    mail_content = render_to_string(
        "permission/perm_handle_mail_template.html",
        context={
            "title": title,
            "api_name": record.gateway.name,
            "bk_app_code": record.bk_app_code,
            "part1_permission": part1_permission,
            "part2_permission": part2_permission,
            "comment": record.comment,
            "grant_dimension_display": GrantDimensionEnum.get_choice_label(record.grant_dimension),
        },
    )

    params = {
        "title": title,
        "receiver__username": record.applied_by,
        "content": mail_content,
        "attachments": [
            {
                "filename": "api_gateway.png",
                "content": base64.b64encode(read_file(APIGW_LOGO_PATH)).decode("utf-8"),
            }
        ],
    }

    return cmsi_component.send_mail(params)


@shared_task(name="apigateway.apps.permission.tasks.renew_app_resource_permission", ignore_result=True)
def renew_app_resource_permission():
    """
    蓝鲸应用访问资源权限自动续期

    - 仅续期未过期的应用资源权限
    """
    # 为防止统计数据获取偏差，时间跨度设置为 2 天
    time_range_days = 2

    time_ = timezone.now() + datetime.timedelta(days=-time_range_days)
    queryset = StatisticsAppRequestByDay.objects.filter(end_time__gt=time_)

    app_request_data = defaultdict(dict)
    for item in queryset:
        if not item.bk_app_code:
            continue
        app_request_data[item.bk_app_code].setdefault(item.gateway_id, set())
        app_request_data[item.bk_app_code][item.gateway_id].add(item.resource_id)

    for bk_app_code, gateway_resources in app_request_data.items():
        for gateway_id, resource_ids in gateway_resources.items():
            AppResourcePermission.objects.renew_not_expired_permissions(
                gateway_id,
                bk_app_code=bk_app_code,
                resource_ids=resource_ids,
                grant_type=GrantTypeEnum.AUTO_RENEW.value,
            )


class AppPermissionExpiringSoonAlerter:
    def __init__(self, expire_in_days: int, expire_day_to_alert: List[int]):
        """
        - param expire_in_days: 统计过期时间在指定天内的权限
        - param expire_day_to_alert: 需要告警的过期天数，只有过期时间在指定天的权限才会告警，防止告警过多
        """
        self.expire_in_days = expire_in_days
        self.expire_day_to_alert = expire_day_to_alert

    def alert(self):
        permissions = self._get_permissions_expiring_soon()

        # 过滤掉不告警的记录
        filtered_permissions = self._filter_permissions(permissions)

        # 不全权限中的网关名、资源名等数据
        self._complete_permissions(filtered_permissions)

        # 发送告警
        self._send_alert(filtered_permissions)

    def _get_permissions_expiring_soon(self) -> Dict[str, List]:
        now = timezone.now()
        expire_end_time = now + datetime.timedelta(days=self.expire_in_days)

        permissions = defaultdict(list)

        # 按网关的权限
        permissions_by_gateway = AppGatewayPermission.objects.filter(expires__range=(now, expire_end_time))
        for permission in permissions_by_gateway:
            permissions[permission.bk_app_code].append(
                {
                    "gateway_id": permission.gateway_id,
                    "expire_days": int(permission.expires_in / ONE_DAY_SECONDS),
                    "grant_dimension": GrantDimensionEnum.API.value,
                    "grant_dimension_display": GrantDimensionEnum.get_choice_label(GrantDimensionEnum.API.value),
                }
            )

        # 按资源的权限
        contexts = Context.objects.filter(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            type=ContextTypeEnum.RESOURCE_AUTH.value,
        )
        resource_ids = [content.scope_id for content in contexts if content.config["resource_perm_required"]]

        permissions_by_resource = AppResourcePermission.objects.filter(
            resource_id__in=resource_ids,
            expires__range=(now, expire_end_time),
        )
        for permission in permissions_by_resource:
            permissions[permission.bk_app_code].append(
                {
                    "gateway_id": permission.gateway_id,
                    "expire_days": int(permission.expires_in / ONE_DAY_SECONDS),
                    "grant_dimension": GrantDimensionEnum.RESOURCE.value,
                    "grant_dimension_display": GrantDimensionEnum.get_choice_label(GrantDimensionEnum.RESOURCE.value),
                    "resource_id": permission.resource_id,
                }
            )

        return permissions

    def _filter_permissions(self, permissions: Dict[str, List]) -> Dict[str, List]:
        """
        - 过滤掉不在指定告警时间的权限
        - 过滤掉已下架网关的权限
        """
        gateway_ids = {perm["gateway_id"] for perms in permissions.values() for perm in perms}
        inactive_gateway_ids = list(
            Gateway.objects.filter(id__in=gateway_ids, status=GatewayStatusEnum.INACTIVE.value).values_list(
                "id", flat=True
            )
        )

        filtered_permissions = defaultdict(list)
        for bk_app_code, app_perms in permissions.items():
            for app_perm in app_perms:
                if app_perm["expire_days"] not in self.expire_day_to_alert:
                    continue

                if app_perm["gateway_id"] in inactive_gateway_ids:
                    continue

                filtered_permissions[bk_app_code].append(app_perm)

        return filtered_permissions

    def _complete_permissions(self, permissions: Dict[str, List]):
        """补全，完善权限数据"""
        gateway_ids = {perm["gateway_id"] for perms in permissions.values() for perm in perms}
        resource_ids = {
            perm["resource_id"] for perms in permissions.values() for perm in perms if perm.get("resource_id")
        }

        # 补全网关名称、资源名称
        gateway_id_to_fields = {
            item["id"]: item for item in Gateway.objects.filter(id__in=gateway_ids).values("id", "name")
        }
        resource_id_to_fields = {
            item["id"]: item for item in Resource.objects.filter(id__in=resource_ids).values("id", "name")
        }
        for app_perms in permissions.values():
            for perm in app_perms:
                perm.update(
                    {
                        "gateway_name": gateway_id_to_fields[perm["gateway_id"]].get("name", ""),
                        "resource_name": resource_id_to_fields.get(perm.get("resource_id"), {}).get("name", ""),
                    }
                )

    def _send_alert(self, permissions: Dict[str, List]):
        for bk_app_code, app_perms in permissions.items():
            app_maintainers = paasv3_component.get_app_maintainers(bk_app_code)
            if not app_maintainers:
                continue

            sorted_app_perms = sorted(
                app_perms, key=lambda x: (x["gateway_name"], x["grant_dimension"], x["resource_name"])
            )

            title = f"【蓝鲸API网关】你的应用【{bk_app_code}】访问网关资源的权限即将过期，请尽快处理"

            mail_content = render_to_string(
                "permission/alert_app_permission_expiring_soon_template.html",
                context={
                    "title": title,
                    "bk_app_code": bk_app_code,
                    "permissions": sorted_app_perms,
                    "renew_permission_link": settings.PAAS_RENEW_API_PERMISSION_URL.format(bk_app_code=bk_app_code),
                },
            )

            params = {
                "title": title,
                "receiver__username": app_maintainers,
                "content": mail_content,
                "attachments": [
                    {
                        "filename": "api_gateway.png",
                        "content": base64.b64encode(read_file(APIGW_LOGO_PATH)).decode("utf-8"),
                    }
                ],
            }

            cmsi_component.send_mail(params)


@shared_task(name="apigateway.apps.permission.tasks.alert_app_permission_expiring_soon", ignore_result=True)
def alert_app_permission_expiring_soon():
    """
    告警通知应用访问网关权限快过期
    - 过期前 15 天开始通知
    - 为防止告警消息过多，只通知指定过期天数，如 0, 1, 3, 7, 15
    """
    alerter = AppPermissionExpiringSoonAlerter(expire_in_days=16, expire_day_to_alert=[0, 1, 3, 7, 15])
    alerter.alert()
