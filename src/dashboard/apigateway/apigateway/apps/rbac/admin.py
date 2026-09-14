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
from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from apigateway.common.admin import AuditFieldsDisplayAdminMixin

from .models import GatewayMember


class GatewayMemberAdmin(AuditFieldsDisplayAdminMixin, DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "gateway", "username", "role", "expires", "updated_time"]
    search_fields = ["username", "gateway__name", "=gateway__id", "created_by", "updated_by"]
    list_filter = ["role", "expires", ("gateway", admin.RelatedOnlyFieldListFilter)]
    raw_id_fields = ["gateway"]
    list_select_related = ["gateway"]
    ordering = ["-updated_time"]


admin.site.register(GatewayMember, GatewayMemberAdmin)
