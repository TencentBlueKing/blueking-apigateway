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

from apigateway.core.constants import ContextScopeTypeEnum
from apigateway.core.models import (
    JWT,
    Backend,
    BackendConfig,
    Context,
    Gateway,
    GatewayRelatedApp,
    MicroGateway,
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
    list_filter = ["status", "is_public"]


class StageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "gateway", "status", "created_by", "updated_by", "created_time", "updated_time"]
    search_fields = ["id", "name", "gateway__id", "gateway__name"]
    list_filter = ["gateway", "status"]


class ResourceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "method", "path", "gateway", "proxy_id", "is_public"]
    search_fields = ["id", "name", "path"]
    list_filter = ["gateway"]


class StageResourceDisabledAdmin(admin.ModelAdmin):
    list_display = ["resource", "stage"]
    search_fields = ["resource__id"]


class ProxyAdmin(admin.ModelAdmin):
    list_display = ["id", "type", "resource", "backend"]
    search_fields = ["resource__id", "resource_name", "id"]


class ResourceVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "version", "schema_version", "created_by", "created_time"]
    search_fields = ["gateway__id", "gateway__name", "version"]
    list_filter = ["gateway"]
    exclude = ["_data"]


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ["gateway", "stage", "resource_version"]
    list_filter = ["gateway"]
    raw_id_fields = ["resource_version"]
    search_fields = ["gateway__id", "gateway__name"]


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
    search_fields = ["resource_version_id", "resource_id", "resource_name", "gateway_name"]


class ReleaseHistoryAdmin(admin.ModelAdmin):
    list_display = ["gateway", "stage", "resource_version", "status", "created_by", "created_time"]
    list_filter = ["gateway", "status", "created_time"]
    search_fields = ["gateway__id", "gateway__name"]
    raw_id_fields = ["resource_version"]


class PublishEventAdmin(admin.ModelAdmin):
    list_display = ["gateway", "stage", "publish_id", "name", "status", "created_by", "created_time"]
    search_fields = ["gateway__id", "gateway__name", "publish_id"]
    list_filter = ["gateway", "status", "name"]


class ContextAdmin(admin.ModelAdmin):
    list_display = ["id", "scope_type", "scope_id", "type"]
    list_filter = ["scope_type", "type"]
    search_fields = ["scope_id"]

    def get_search_results(self, request, queryset, search_term):
        # 根据网关名称搜索结果，同时保留过滤器条件
        queryset, use_distinct = super().get_search_results(request, queryset, "")

        if not search_term:
            return queryset, use_distinct

        gateway_obj = Gateway.objects.filter(name=search_term).first()
        if not gateway_obj:
            # 没有查询到网关信息，返回空的 queryset
            return self.model.objects.none(), use_distinct

        # 查询 GATEWAY 类型的记录
        gateway_queryset = queryset.filter(scope_type=ContextScopeTypeEnum.GATEWAY.value, scope_id=gateway_obj.id)

        # 查询 STAGE 类型的记录
        stage_ids = list(Stage.objects.filter(gateway=gateway_obj).values_list("id", flat=True))
        stage_queryset = queryset.filter(scope_type=ContextScopeTypeEnum.STAGE.value, scope_id__in=stage_ids)

        # 查询 RESOURCE 类型的记录
        resource_ids = list(Resource.objects.filter(gateway=gateway_obj).values_list("id", flat=True))
        resource_queryset = queryset.filter(scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id__in=resource_ids)

        queryset = gateway_queryset | stage_queryset | resource_queryset

        return queryset, use_distinct


class JWTAdmin(admin.ModelAdmin):
    list_display = ["gateway"]
    search_fields = ["gateway__id", "gateway__name"]
    exclude = ["private_key"]


class GatewayRelatedAppAdmin(admin.ModelAdmin):
    list_display = ["gateway", "bk_app_code"]
    search_fields = ["gateway__id", "gateway__name", "bk_app_code"]
    list_filter = ["gateway"]


class MicroGatewayAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "name", "is_shared", "status", "updated_time"]


class BackendAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "type", "name", "description"]
    search_fields = ["name", "gateway__id", "gateway__name", "description"]
    list_filter = ["gateway"]


class BackendConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "gateway", "backend", "stage", "config"]
    search_fields = ["gateway__id", "gateway__name", "backend_id"]
    list_filter = ["gateway", "backend", "stage"]


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
admin.site.register(Backend, BackendAdmin)
admin.site.register(BackendConfig, BackendConfigAdmin)
