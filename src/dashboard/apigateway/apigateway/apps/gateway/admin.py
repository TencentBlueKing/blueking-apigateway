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
from apigw_manager.apigw.admin import ContextAdmin as BaseContextAdmin
from apigw_manager.apigw.models import Context
from django.contrib import admin
from django_celery_beat.admin import (
    ClockedScheduleAdmin as BaseClockedScheduleAdmin,
)
from django_celery_beat.admin import (
    CrontabScheduleAdmin as BaseCrontabScheduleAdmin,
)
from django_celery_beat.admin import (
    IntervalScheduleAdmin as BaseIntervalScheduleAdmin,
)
from django_celery_beat.admin import (
    PeriodicTaskAdmin as BasePeriodicTaskAdmin,
)
from django_celery_beat.admin import (
    SolarScheduleAdmin as BaseSolarScheduleAdmin,
)
from django_celery_beat.models import ClockedSchedule, CrontabSchedule, IntervalSchedule, PeriodicTask, SolarSchedule
from djangoql.admin import DjangoQLSearchMixin

from .models import GatewayAppBinding


class GatewayAppBindingAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "gateway", "bk_app_code", "updated_time"]
    search_fields = ["gateway__id", "bk_app_code"]
    list_filter = ["gateway"]


class ContextAdmin(DjangoQLSearchMixin, BaseContextAdmin):
    """
    继承原有 ContextAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["scope", "key", "value"]


class PeriodicTaskAdmin(DjangoQLSearchMixin, BasePeriodicTaskAdmin):
    """
    继承原有 PeriodicTaskAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["name"]


class ClockedScheduleAdmin(DjangoQLSearchMixin, BaseClockedScheduleAdmin):
    """
    继承原有 BaseClockedScheduleAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["clocked_time"]


class SolarScheduleAdmin(DjangoQLSearchMixin, BaseSolarScheduleAdmin):
    """
    继承原有 SolarScheduleAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["event"]


class CrontabScheduleAdmin(DjangoQLSearchMixin, BaseCrontabScheduleAdmin):
    """
    继承原有 CrontabScheduleAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["minute", "hour", "day_of_month", "month_of_year", "day_of_week"]


class IntervalScheduleAdmin(DjangoQLSearchMixin, BaseIntervalScheduleAdmin):
    """
    继承原有 IntervalScheduleAdmin 并添加 DjangoQL 功能
    保持所有原有配置不变，只增加搜索功能
    """

    djangoql_completion_enabled_by_default = False
    search_fields = ["period"]


admin.site.register(GatewayAppBinding, GatewayAppBindingAdmin)

# 取消原有的注册
admin.site.unregister(Context)
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)

# 自定义 Admin 类重新注册
admin.site.register(Context, ContextAdmin)
admin.site.register(PeriodicTask, PeriodicTaskAdmin)
admin.site.register(IntervalSchedule, IntervalScheduleAdmin)
admin.site.register(CrontabSchedule, CrontabScheduleAdmin)
admin.site.register(SolarSchedule, SolarScheduleAdmin)
admin.site.register(ClockedSchedule, ClockedScheduleAdmin)
