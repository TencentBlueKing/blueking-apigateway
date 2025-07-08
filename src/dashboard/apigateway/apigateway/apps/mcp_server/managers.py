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
from typing import List

from django.db import models

from apigateway.common.time import calculate_renew_time


class MCPServerAppPermissionManager(models.Manager):
    def save_permission(self, mcp_server_id: int, bk_app_code: str, grant_type: str, expire_days=None):
        self.update_or_create(
            mcp_server_id=mcp_server_id,
            bk_app_code=bk_app_code,
            grant_type=grant_type,
            defaults={
                "expires": calculate_renew_time(expire_days),
            },
        )


class MCPServerAppPermissionApplyManager(models.Manager):
    def filter_app_permission_apply(self, queryset, status_list: List[str], bk_app_code: str, applied_by: str):
        queryset = queryset.filter(status__in=status_list)

        if bk_app_code:
            queryset = queryset.filter(bk_app_code__icontains=bk_app_code)
        if applied_by:
            queryset = queryset.filter(applied_by=applied_by)

        return queryset
