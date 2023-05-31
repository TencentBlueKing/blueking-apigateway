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
import logging
from collections import defaultdict

import arrow
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from apigateway.apps.metrics.stats_helpers import StatisticsAppRequestByResourceMetrics
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
from apigateway.core.models import Gateway
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
    """
    # 统计前一天的请求数据，为防止临界时间点的数据统计不到，时间跨度设置为 25 小时
    _, end = arrow.utcnow().shift(days=-1).span("day")
    step = "25h"

    app_request_count = StatisticsAppRequestByResourceMetrics().query(end.float_timestamp, step)
    if not app_request_count.result:
        logger.error("statistics app requests by resource to renew app resource permission fail.")
        return

    app_api_resources = {}
    for item in app_request_count.result:
        count = float(item.value[1])
        if count <= 0:
            continue

        # 部分资源不认证应用
        if not item.metric.get("app_code"):
            continue

        app_api_resources.setdefault(item.metric["app_code"], defaultdict(list))
        app_api_resources[item.metric["app_code"]][item.metric["api"]].append(int(item.metric["resource"]))

    for bk_app_code, api_resources in app_api_resources.items():
        for gateway_id, resource_ids in api_resources.items():
            gateway = Gateway.objects.filter(id=int(gateway_id)).first()
            if not gateway:
                logger.warning(f"api[id={gateway_id}] not exist, renew app resource permission fail")
                continue

            # 如果应用-资源权限不存在，则将按网关的权限同步到应用-资源权限
            AppResourcePermission.objects.sync_from_gateway_permission(
                gateway,
                bk_app_code=bk_app_code,
                resource_ids=resource_ids,
            )

            AppResourcePermission.objects.renew_permission(
                gateway,
                bk_app_code=bk_app_code,
                resource_ids=resource_ids,
                grant_type=GrantTypeEnum.AUTO_RENEW.value,
            )
