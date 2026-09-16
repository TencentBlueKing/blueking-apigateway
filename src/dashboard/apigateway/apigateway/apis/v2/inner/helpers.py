# -*- coding: utf-8 -*-
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
"""Helpers for inner API response shaping."""

from django.conf import settings

from apigateway.service.bk_itsm import ItsmPermissionApplyHelper


def build_gateway_permission_approval_url(gateway_id: int, itsm_ticket_id: str) -> str:
    """优先返回 ITSM 工单地址，否则返回网关权限审批页。"""
    itsm_url = ItsmPermissionApplyHelper.build_ticket_url(itsm_ticket_id)
    return itsm_url or f"{settings.DASHBOARD_FE_URL}/{gateway_id}/permission/apply"
