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
from djangoql.admin import DjangoQLSearchMixin

from . import models


class AlarmFilterConfigAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["alarm_type", "gateway"]
    list_filter = ["gateway", "alarm_type"]


class AlarmStrategyAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = (
        "id",
        "gateway",
        "name",
        "alarm_type",
        "alarm_subtype",
        "enabled",
    )
    list_filter = ["gateway", "alarm_type", "alarm_subtype"]
    search_fields = ("name", "gateway__id", "gateway__name")
    filter_horizontal = ["api_labels"]


class AlarmRecordAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = (
        "gateway",
        "alarm_attr_id",
        "alarm_id",
        "source_time",
        "status",
    )
    filter_horizontal = ["alarm_strategies"]
    list_filter = ["gateway", "status"]


admin.site.register(models.AlarmFilterConfig, AlarmFilterConfigAdmin)
admin.site.register(models.AlarmStrategy, AlarmStrategyAdmin)
admin.site.register(models.AlarmRecord, AlarmRecordAdmin)
