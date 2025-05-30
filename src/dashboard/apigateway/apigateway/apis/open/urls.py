# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from django.conf import settings
from django.urls import include, path

# FIXME: 目前根据鉴权应该将接口分为 3 类，目前 3 类是混在一起的，并不好维护
# 按照鉴权分：
# 1. OpenAPIPermission
# 仅验证来自于网关的请求
#     适用：申请网关接口权限后，就能访问的接口，路径参数中没有 gateway_id or gateway_name
#
# 2. OpenAPIGatewayIdPermission
# 验证来自于网关的请求，并且路径参数中有 gateway_id, 且这个 gateway_id 对应网关存在
#     适用：申请网关接口权限后 + 路径参数中 gateway_id 的接口
#
# 3. OpenAPIGatewayNamePermission
# 验证来自于网关的请求，并且路径参数中有 gateway_name, 且这个 gateway_name 对应网关存在
#     适用：申请网关接口权限后 + 路径参数中 gateway_name 的接口
#
# 4. OpenAPIGatewayRelatedAppPermission
# 验证来自于网关的请求 + 路径参数中有 gateway_name, 且这个 gateway_name 对应网关存在 + 这个应用有操作这个网关的权限 (GatewayRelatedApp)
#     适用：SDK 使用的 API，某个应用通过网关的接口对网关进行变更

# 按照用途分
# 1. open api，申请权限的普通应用能用
# 2. inner api, 给 paasv3 定制的专用 api (范围更广)

# 其他问题
# 1. 目前暴露的 url 是  /apis/{api_name}
# 2. 目前这里的 include 非常乱，不好快速定位到目标


# inner 只用到这 16 个，其他的先删除
# allow_apply_by_api_2
# apply_esb_component_permissions
# apply_resource_permission_2
# get_api_resources
# get_apis
# get_app_component_systems
# get_app_permission_apply_record
# get_app_permission_apply_records
# get_esb_systems
# get_system_permission_components
# list_app_resource_permissions
# list_resource_permission_apply_records
# monitor_alarm_callback
# renew_esb_component_permissions
# renew_resource_permission_3
# retrieve_resource_permission_apply_record
# get_api  还没用到，但是会用到

# FIXME: 新版 /api/v2 网关
# 1. 起一个新目录 openv2 统一放代码
# 2. 使用新的协议，废弃旧的协议
# 3. 统一 apis 改成 gateways, api_name 改成 gateway_name
# 4. /api/v2/gateways/{gateway_name}/  开头
# 5. 合并成同一套网关 bk-apigateway，去掉 bk-apigateway-inner, 给 inner 用的接口隐藏 + 主动授权


urlpatterns = [
    # NOTE: deprecated
    path("apis/", include("apigateway.apis.open.gateway.urls")),
    path("", include("apigateway.apis.open.released.urls")),
    path("", include("apigateway.apis.open.support.urls")),
    path("", include("apigateway.apis.open.resource_doc.urls")),
    path("", include("apigateway.apis.open.permission.urls")),
    path("", include("apigateway.apis.open.stage.urls")),
    path("", include("apigateway.apis.open.resource.urls")),
    path("", include("apigateway.apis.open.resource_version.urls")),
    path("", include("apigateway.apis.open.monitor.urls")),
]

# 非多租户模式才会有 esb 相关的接口
if not settings.ENABLE_MULTI_TENANT_MODE:
    from apigateway.apis.open.esb.permission import views as esb_permission_views

    urlpatterns += [
        path("esb/systems/", include("apigateway.apis.open.esb.system.urls")),
        path("esb/systems/<int:system_id>/permissions/", include("apigateway.apis.open.esb.permission.urls")),
        path(
            "esb/systems/permissions/renew/",
            esb_permission_views.AppPermissionRenewAPIView.as_view({"post": "renew"}),
            name="openapi.esb.permission.renew",
        ),
        path(
            "esb/systems/permissions/app-permissions/",
            esb_permission_views.AppPermissionViewSet.as_view({"get": "list"}),
            name="openapi.esb.permission.app-permissions",
        ),
        path(
            "esb/systems/permissions/apply-records/",
            esb_permission_views.AppPermissionApplyRecordViewSet.as_view({"get": "list"}),
            name="openapi.esb.permission.app-records",
        ),
        path(
            "esb/systems/permissions/apply-records/<int:record_id>/",
            esb_permission_views.AppPermissionApplyRecordViewSet.as_view({"get": "retrieve"}),
            name="openapi.esb.permission.app-record-detail",
        ),
    ]
