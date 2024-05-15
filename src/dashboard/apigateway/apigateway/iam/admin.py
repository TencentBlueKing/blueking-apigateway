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
from django.contrib import admin

from apigateway.iam.models import IAMGradeManager, IAMUserGroup


class IAMGradeManagerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "gateway",
        "grade_manager_id",
    ]
    search_fields = ["gateway__id", "gateway__name", "grade_manager_id"]
    list_filter = ["gateway"]


class IAMUserGroupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "gateway",
        "role",
        "user_group_id",
    ]
    search_fields = ["gateway__id", "gateway__name", "grade_manager_id"]
    list_filter = ["gateway", "role"]


admin.site.register(IAMGradeManager, IAMGradeManagerAdmin)
admin.site.register(IAMUserGroup, IAMUserGroupAdmin)
