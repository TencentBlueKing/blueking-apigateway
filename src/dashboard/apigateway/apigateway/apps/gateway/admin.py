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
from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin
from django_celery_beat.models import PeriodicTask
from djangoql.admin import DjangoQLSearchMixin

from .models import GatewayAppBinding


class GatewayAppBindingAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "gateway", "bk_app_code", "updated_time"]
    search_fields = ["gateway__id", "bk_app_code"]
    list_filter = ["gateway"]


class PeriodicTaskAdmin(DjangoQLSearchMixin, BasePeriodicTaskAdmin):
    """
    继承原有 PeriodicTaskAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["name"]


admin.site.register(GatewayAppBinding, GatewayAppBindingAdmin)
admin.site.unregister(PeriodicTask)
admin.site.register(PeriodicTask, PeriodicTaskAdmin)
