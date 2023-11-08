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

from apigateway.core.models import (
    JWT,
    APIRelatedApp,
    BackendService,
    Context,
    Gateway,
    MicroGateway,
    MicroGatewayReleaseHistory,
    Proxy,
    PublishEvent,
    Release,
    ReleasedResource,
    ReleaseHistory,
    Resource,
    ResourceVersion,
    SslCertificate,
    SslCertificateBinding,
    Stage,
    StageItem,
    StageItemConfig,
    StageResourceDisabled,
)


class GatewayAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "status",
        "is_public",
        "hosting_type",
        "created_by",
        "created_time",
        "updated_time",
    ]
    search_fields = ["id", "name"]


class StageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "api", "status", "created_by", "updated_by", "created_time", "updated_time"]
    search_fields = ["id", "name"]
    list_filter = ["api"]


class StageItemAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "api", "type", "updated_time"]
    search_fields = ["id", "name"]
    list_filter = ["api"]


class StageItemConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "api", "stage", "stage_item"]
    search_fields = ["id"]
    list_filter = ["api"]


class ResourceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "method", "path", "api", "proxy_id", "is_public"]
    search_fields = ["id", "name", "path"]
    list_filter = ["api"]


class StageResourceDisabledAdmin(admin.ModelAdmin):
    list_display = ["resource", "stage"]
    search_fields = ["resource__id"]


class ProxyAdmin(admin.ModelAdmin):
    list_display = ["id", "type", "resource"]
    search_fields = ["resource__id", "id"]


class ResourceVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "title", "api", "created_by", "created_time"]
    search_fields = ["name"]
    list_filter = ["api"]
    exclude = ["_data"]


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ["api", "stage", "resource_version"]
    list_filter = ["api"]
    raw_id_fields = ["resource_version"]


class ReleasedResourceAdmin(admin.ModelAdmin):
    list_display = ["api", "resource_version_id", "resource_id", "resource_name", "resource_method", "resource_path"]
    list_filter = ["api"]
    search_fields = ["resource_version_id", "resource_id", "resource_name"]


class ReleaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["api", "resource_version", "status", "created_by", "created_time"]
    list_filter = ["api", "created_time"]
    filter_horizontal = ["stages"]
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
    list_display = ["api"]
    search_fields = ["api__id"]
    exclude = ["private_key"]


class APIRelatedAppAdmin(admin.ModelAdmin):
    list_display = ["api", "bk_app_code"]
    search_fields = ["api__id", "bk_app_code"]
    list_filter = ["api"]


class MicroGatewayAdmin(admin.ModelAdmin):
    list_display = ["id", "api", "name", "is_shared", "status", "updated_time"]


class MicroGatewayReleaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "api", "stage", "micro_gateway", "status"]
    list_filter = ["api"]
    raw_id_fields = ["release_history"]


class BackendServiceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "api", "upstream_type", "updated_time"]
    search_fields = ["name"]
    list_filter = ["api"]


class SslCertificateAdmin(admin.ModelAdmin):
    list_display = ["id", "api", "name", "type", "expires", "updated_time"]
    search_fields = ["name"]
    list_filter = ["api"]


class SslCertificateBindingAdmin(admin.ModelAdmin):
    list_display = ["id", "api", "scope_type", "scope_id", "ssl_certificate_id"]
    search_fields = ["scope_id", "ssl_certificate_id"]
    list_filter = ["api"]


admin.site.register(Gateway, GatewayAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(StageItem, StageItemAdmin)
admin.site.register(StageItemConfig, StageItemConfigAdmin)
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
admin.site.register(APIRelatedApp, APIRelatedAppAdmin)
admin.site.register(MicroGateway, MicroGatewayAdmin)
admin.site.register(MicroGatewayReleaseHistory, MicroGatewayReleaseHistoryAdmin)
admin.site.register(BackendService, BackendServiceAdmin)
admin.site.register(SslCertificate, SslCertificateAdmin)
admin.site.register(SslCertificateBinding, SslCertificateBindingAdmin)
