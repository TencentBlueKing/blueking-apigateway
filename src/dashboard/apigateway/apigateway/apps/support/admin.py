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

from apigateway.apps.support.models import GatewaySDK, ReleasedResourceDoc, ResourceDoc, ResourceDocVersion


class ResourceDocAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "resource_id", "language", "source", "updated_by", "updated_time"]
    search_fields = ["id", "resource_id"]
    list_filter = ["gateway", "language"]


class ResourceDocVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "resource_version"]
    list_filter = ["gateway"]
    exclude = ["_data"]
    raw_id_fields = ["resource_version"]


class ReleasedResourceDocAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "resource_version_id", "resource_id", "language"]
    list_filter = ["gateway", "language"]
    search_fields = ["resource_id"]


class APISDKAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "gateway",
        "resource_version_id",
        "name",
        "language",
        "version_number",
        "is_recommended",
        "is_public",
        "created_time",
    ]
    list_filter = ["gateway"]
    search_fields = ["version_number"]
    raw_id_fields = ["resource_version"]


admin.site.register(ResourceDoc, ResourceDocAdmin)
admin.site.register(ResourceDocVersion, ResourceDocVersionAdmin)
admin.site.register(GatewaySDK, APISDKAdmin)
admin.site.register(ReleasedResourceDoc, ReleasedResourceDocAdmin)
