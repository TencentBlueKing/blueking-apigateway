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
from django.contrib import admin

from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding, IPGroup


class IPGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "api"]
    search_fields = ["name"]
    list_filter = ["api"]


class AccessStrategyAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "api"]
    search_fields = ["name"]
    list_filter = ["type", "api"]


class AccessStrategyBindingAdmin(admin.ModelAdmin):
    list_display = ["id", "scope_type", "scope_id", "type", "access_strategy"]
    search_fields = ["scope_id"]
    list_filter = ["scope_type", "type"]


admin.site.register(IPGroup, IPGroupAdmin)
admin.site.register(AccessStrategy, AccessStrategyAdmin)
admin.site.register(AccessStrategyBinding, AccessStrategyBindingAdmin)
