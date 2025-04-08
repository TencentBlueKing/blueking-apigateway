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

from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg import openapi as parameters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, serializers, status

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.biz.backend import BackendHandler
from apigateway.biz.plugin_binding import PluginBindingHandler
from apigateway.biz.resource_version import ResourceDocVersionHandler, ResourceVersionHandler
from apigateway.biz.resource_version_diff import ResourceDifferHandler
from apigateway.biz.sdk.gateway_sdk import GatewaySDKHandler
from apigateway.core.models import Release, Resource, ResourceVersion
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.version import get_next_version

from .serializers import (
    NeedNewVersionOutputSLZ,
    ResourceVersionCreateInputSLZ,
    ResourceVersionDiffOutputSLZ,
    ResourceVersionDiffQueryInputSLZ,
    ResourceVersionListInputSLZ,
    ResourceVersionListOutputSLZ,
    ResourceVersionRetrieveOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ResourceVersionListOutputSLZ(many=True)},
        tags=["WebAPI.ResourceVersion"],
        operation_description="资源版本列表查询接口",
        query_serializer=ResourceVersionListInputSLZ(),
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        request_body=ResourceVersionCreateInputSLZ,
        tags=["WebAPI.ResourceVersion"],
        operation_description="资源版本创建接口",
    ),
)
class ResourceVersionListCreateApi(generics.ListCreateAPIView):
    lookup_field = "id"
    serializer_class = ResourceVersionCreateInputSLZ

    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway).order_by("-id")

    def list(self, request, *args, **kwargs):
        slz = ResourceVersionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        query = slz.validated_data.get("keyword")
        queryset = ResourceVersion.objects.filter(gateway=request.gateway)
        if query:
            queryset = queryset.filter(version__icontains=query)
        data = queryset.values("id", "version", "schema_version", "comment", "created_time", "created_by").order_by(
            "-id"
        )

        page = self.paginate_queryset(data)
        resource_version_ids = [rv["id"] for rv in page]

        slz = ResourceVersionListOutputSLZ(
            page,
            many=True,
            context={
                "released_stages": Release.objects.get_released_stages(request.gateway, resource_version_ids),
                "resource_version_ids_sdk_count": GatewaySDKHandler.get_resource_version_sdk_count_map(
                    resource_version_ids
                ),
            },
        )
        return self.get_paginated_response(slz.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = self.serializer_class(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        instance = ResourceVersionHandler.create_resource_version(request.gateway, slz.data, request.user.username)

        # 创建文档版本
        if ResourceDoc.objects.filter(gateway=request.gateway).exists():
            ResourceDocVersion.objects.create(
                gateway=self.request.gateway,
                resource_version=instance,
                data=ResourceDocVersion.objects.make_version(request.gateway.id),
            )

        # 创建resource_schema版本

        return OKJsonResponse(status=status.HTTP_201_CREATED)


class ResourceVersionRetrieveApi(generics.RetrieveAPIView):
    serializer_class = ResourceVersionRetrieveOutputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway)

    @method_decorator(
        name="get",
        decorator=swagger_auto_schema(
            tags=["WebAPI.ResourceVersion"],
            operation_description="资源版本详情查询接口",
            manual_parameters=[
                # 定义一个名为 "query" 的查询参数，默认值为 "None"
                parameters.Parameter(
                    name="stage_id",
                    in_=parameters.IN_QUERY,
                    type=parameters.TYPE_INTEGER,
                    description="stage_id",
                    default="None",
                )
            ],
        ),
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        # 查询资源文档的更新时间
        resource_docs_updated_time = ResourceDocVersion.objects.get_doc_updated_time(request.gateway.id, instance.id)

        # 查询网关后端服务
        resource_backends = BackendHandler.get_id_to_instance(request.gateway.id)

        context = {
            "resource_doc_updated_time": resource_docs_updated_time,
            "resource_backends": resource_backends,
            "is_schema_v2": instance.is_schema_v2,
        }

        # 如果传入了stage,返回对应stage的backend_config以及合并资源插件
        stage_id = self.request.query_params.get("stage_id")

        if stage_id:
            backend_configs = BackendHandler.get_backend_configs_by_stage(request.gateway.id, stage_id)
            context["resource_backend_configs"] = backend_configs

            stage_plugins = {}
            stage_plugin_bindings = PluginBindingHandler.get_stage_plugin_bindings(request.gateway.id, stage_id)
            # 列表需要展示资源生效插件，此时需要返回环境绑定的插件信息
            for plugin_type, plugin_binding in stage_plugin_bindings.items():
                plugin_config = plugin_binding.snapshot()
                plugin_config["binding_type"] = PluginBindingScopeEnum.STAGE.value
                stage_plugins[plugin_type] = plugin_config
            context["stage_plugins"] = stage_plugins

        slz = ResourceVersionRetrieveOutputSLZ(instance, context=context)

        return OKJsonResponse(data=slz.data)


class ResourceVersionNeedNewVersionRetrieveApi(generics.RetrieveAPIView):
    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway).order_by("-id")

    @method_decorator(
        name="get",
        decorator=swagger_auto_schema(
            responses={status.HTTP_200_OK: NeedNewVersionOutputSLZ()},
            tags=["WebAPI.ResourceVersion"],
            operation_description="是否需要创建新资源版本查询接口",
        ),
    )
    def get(self, request, *args, **kwargs):
        resource_version_exist = ResourceVersion.objects.filter(gateway_id=request.gateway.id).exists()
        resource_exist = Resource.objects.filter(gateway_id=request.gateway.id).exists()
        if not (resource_version_exist or resource_exist):
            raise serializers.ValidationError(_("请先创建资源，然后再发布版本。"))

        if ResourceVersionHandler.need_new_version(request.gateway.id):
            return OKJsonResponse(
                data={"need_new_version": True, "msg": _("资源有更新，需生成新版本并发布到指定环境，才能生效。")},
            )

        if ResourceDocVersionHandler.need_new_version(request.gateway.id):
            return OKJsonResponse(
                data={"need_new_version": True, "msg": _("资源文档有更新，需生成新版本并发布到任一环境，才能生效。")},
            )

        return OKJsonResponse(data={"need_new_version": False})


class ResourceVersionDiffRetrieveApi(generics.RetrieveAPIView):
    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway)

    @method_decorator(
        name="get",
        decorator=swagger_auto_schema(
            query_serializer=ResourceVersionDiffQueryInputSLZ(),
            responses={status.HTTP_200_OK: ResourceVersionDiffOutputSLZ()},
            tags=["WebAPI.ResourceVersion"],
            operation_description="资源版本对比接口",
        ),
    )
    def get(self, request, *args, **kwargs):
        """
        版本对比
        """
        slz = ResourceVersionDiffQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        source_resource_version_id = data.get("source_resource_version_id")
        target_resource_version_id = data.get("target_resource_version_id")

        version = ResourceVersionHandler.get_latest_version_by_gateway(request.gateway.id)

        source_resource_data = []
        # 如果 source_resource_version_id不为空，并且不是第一次生成版本
        if source_resource_version_id and version != "":
            source_resource_data = ResourceVersionHandler.get_data_by_id_or_new(
                request.gateway, source_resource_version_id
            )

        target_resource_data = ResourceVersionHandler.get_data_by_id_or_new(
            request.gateway, target_resource_version_id
        )

        data = ResourceDifferHandler.diff_resource_version_data(
            source_resource_data,
            target_resource_data,
            source_resource_doc_updated_time=ResourceDocVersion.objects.get_doc_updated_time(
                request.gateway.id, data.get("source_resource_version_id")
            ),
            target_resource_doc_updated_time=ResourceDocVersion.objects.get_doc_updated_time(
                request.gateway.id, data.get("target_resource_version_id")
            ),
        )

        return OKJsonResponse(
            data=data,
        )


class NextResourceVersionRetrieveApi(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        query_set = ResourceVersion.objects.filter(gateway=request.gateway).order_by("-id")
        obj = query_set.first()
        if obj:
            new_version_str = get_next_version(obj.version)
            return OKJsonResponse(
                data={"version": new_version_str},
            )
        return OKJsonResponse(
            data={"version": "1.0.0"},
        )
