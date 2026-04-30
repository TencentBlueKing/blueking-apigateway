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
from django.contrib import admin

from apigateway.apps.bk_itsm.models import ItsmSystemConfig


@admin.register(ItsmSystemConfig)
class ItsmSystemConfigAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "system_code",
        "system_name",
        "itsm_system_id",
        "workflow_key",
        "workflow_name",
        "portal_id",
        "is_registered",
        "created_time",
        "updated_time",
    ]
    list_filter = ["is_registered", "portal_id"]
    search_fields = ["system_code", "system_name", "itsm_system_id", "workflow_key", "workflow_name"]
    readonly_fields = ["created_time", "updated_time"]
