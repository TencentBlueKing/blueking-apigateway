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
from typing import List

from django.contrib import admin

from apigateway.core.models import (
    JWT,
    Backend,
    BackendConfig,
    Context,
    Gateway,
    GatewayRelatedApp,
    MicroGateway,
    MicroGatewayReleaseHistory,
    Proxy,
    PublishEvent,
    Release,
    ReleasedResource,
    ReleaseHistory,
    Resource,
    ResourceVersion,
    Stage,
    StageResourceDisabled,
)


class GatewayAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "status",
        "is_public",
        "created_by",
        "created_time",
        "updated_time",
    ]
    search_fields = ["id", "name"]


class StageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "gateway", "status", "created_by", "updated_by", "created_time", "updated_time"]
    search_fields = ["id", "name"]
    list_filter = ["gateway"]


class ResourceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "method", "path", "gateway", "proxy_id", "is_public"]
    search_fields = ["id", "name", "path"]
    list_filter = ["gateway"]


class StageResourceDisabledAdmin(admin.ModelAdmin):
    list_display = ["resource", "stage"]
    search_fields = ["resource__id"]


class ProxyAdmin(admin.ModelAdmin):
    list_display = ["id", "type", "resource"]
    search_fields = ["resource__id", "id"]


class ResourceVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "title", "gateway", "created_by", "created_time"]
    search_fields = ["name"]
    list_filter = ["gateway"]
    exclude = ["_data"]


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ["gateway", "stage", "resource_version"]
    list_filter = ["gateway"]
    raw_id_fields = ["resource_version"]


class ReleasedResourceAdmin(admin.ModelAdmin):
    list_display = [
        "gateway",
        "resource_version_id",
        "resource_id",
        "resource_name",
        "resource_method",
        "resource_path",
    ]
    list_filter = ["gateway"]
    search_fields = ["resource_version_id", "resource_id", "resource_name"]


class ReleaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["gateway", "resource_version", "status", "created_by", "created_time"]
    list_filter = ["gateway", "created_time"]
    search_fields = ["stage_id"]
    raw_id_fields = ["resource_version"]


class PublishEventAdmin(admin.ModelAdmin):
    list_display = ["gateway_id", "stage_id", "publish_id", "name", "status", "created_by", "created_time"]
    list_filter = ["gateway_id"]
    search_fields = ["gateway_id", "publish_id"]


class ContextAdmin(admin.ModelAdmin):
    list_display = ["id", "scope_type", "scope_id", "type"]
    list_filter = ["scope_type", "type"]
    search_fields = ["scope_id"]


class JWTAdmin(admin.ModelAdmin):
    list_display = ["gateway"]
    search_fields = ["gateway__id"]
    exclude = ["private_key"]


class GatewayRelatedAppAdmin(admin.ModelAdmin):
    list_display = ["gateway", "bk_app_code"]
    search_fields = ["gateway__id", "bk_app_code"]
    list_filter = ["gateway"]


class MicroGatewayAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "name", "is_shared", "status", "updated_time"]


class MicroGatewayReleaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "stage", "micro_gateway", "status"]
    list_filter = ["gateway"]
    raw_id_fields = ["release_history"]


class BackendAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "type", "name", "description"]
    search_fields = ["name"]
    list_filter = ["gateway"]


class BackendConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "backend", "stage", "config"]
    search_fields: List[str] = []
    list_filter = ["gateway", "backend", "stage"]


class SslCertificateAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "name", "type", "expires", "updated_time"]
    search_fields = ["name"]
    list_filter = ["gateway"]


class SslCertificateBindingAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "scope_type", "scope_id", "ssl_certificate_id"]
    search_fields = ["scope_id", "ssl_certificate_id"]
    list_filter = ["gateway"]


admin.site.register(Gateway, GatewayAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(StageResourceDisabled, StageResourceDisabledAdmin)
admin.site.register(Proxy, ProxyAdmin)
admin.site.register(ResourceVersion, ResourceVersionAdmin)
admin.site.register(Release, ReleaseAdmin)
admin.site.register(ReleasedResource, ReleasedResourceAdmin)
admin.site.register(ReleaseHistory, ReleaseHistoryAdmin)
admin.site.register(PublishEvent, PublishEventAdmin)
admin.site.register(Context, ContextAdmin)
admin.site.register(JWT, JWTAdmin)
admin.site.register(GatewayRelatedApp, GatewayRelatedAppAdmin)
admin.site.register(MicroGateway, MicroGatewayAdmin)
admin.site.register(MicroGatewayReleaseHistory, MicroGatewayReleaseHistoryAdmin)
admin.site.register(Backend, BackendAdmin)
admin.site.register(BackendConfig, BackendConfigAdmin)
