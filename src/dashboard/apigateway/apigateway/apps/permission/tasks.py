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
from collections import defaultdict

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apigateway.apps.metrics.models import StatisticsAppRequestByDay
from apigateway.apps.permission.constants import (
    APIGW_LOGO_PATH,
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.helpers import PermissionDimensionManager
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord, AppResourcePermission
from apigateway.components.cmsi import cmsi_component
from apigateway.utils.file import read_file

logger = logging.getLogger(__name__)


@shared_task(name="apigateway.apps.permission.tasks.send_mail_for_perm_apply", ignore_result=True)
def send_mail_for_perm_apply(record_id):
    """
    申请权限，发送邮件通知管理员审批
    """
    record = AppPermissionApply.objects.get(id=record_id)

    apigw_domain = getattr(settings, "DASHBOARD_FE_URL", "").rstrip("/")
    manager = PermissionDimensionManager.get_manager(record.grant_dimension)

    title = f"【蓝鲸API网关】蓝鲸应用【{record.bk_app_code}】访问网关资源权限申请"

    mail_content = render_to_string(
        "permission/perm_apply_mail_template.html",
        context={
            "title": title,
            "api_name": record.api.name,
            "bk_app_code": record.bk_app_code,
            "expire_days_display": PermissionApplyExpireDaysEnum.get_choice_label(record.expire_days),
            "grant_dimension_display": GrantDimensionEnum.get_choice_label(record.grant_dimension),
            "resource_names": sorted(manager.get_resource_names_display(record.api.id, record.resource_ids)),
            "perm_apply_link": f"{apigw_domain}/{record.api_id}/permission/applys",
        },
    )

    params = {
        "title": title,
        "receiver__username": ";".join(record.api.maintainers),
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
            record.api.id,
            handled_resource_ids.get(ApplyStatusEnum.APPROVED.value),
            record.status,
        )
    )

    rejected_resource_names = sorted(
        manager.get_rejected_resource_names_display(
            record.api.id,
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

    title = f"【蓝鲸API网关】你对网关【{record.api.name}】资源访问权限的申请已完成"

    mail_content = render_to_string(
        "permission/perm_handle_mail_template.html",
        context={
            "title": title,
            "api_name": record.api.name,
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
        app_request_data[item.bk_app_code].setdefault(item.api_id, set())
        app_request_data[item.bk_app_code][item.api_id].add(item.resource_id)

    for bk_app_code, gateway_resources in app_request_data.items():
        for gateway_id, resource_ids in gateway_resources.items():
            AppResourcePermission.objects.renew_not_expired_permissions(
                gateway_id,
                bk_app_code=bk_app_code,
                resource_ids=resource_ids,
                grant_type=GrantTypeEnum.AUTO_RENEW.value,
            )
