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
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.plugin.models import PluginConfig, PluginForm, PluginType
from apigateway.apps.plugin.plugin import serializers
from apigateway.common.error_codes import error_codes
from apigateway.utils.filterset import SerializerFilterBackend
from apigateway.utils.responses import ResponseRender


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        query_serializer=serializers.PluginConfigFilterSLZ,
        operation_description="list the plugin configs",
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        operation_description="create the plugin config",
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        operation_description="get the plugin config details",
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        operation_description="update the plugin config",
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        operation_description="destroy the plugin config",
    ),
)
class PluginConfigViewSet(viewsets.ModelViewSet):
    renderer_classes = [ResponseRender, BrowsableAPIRenderer]
    serializer_class = serializers.PluginConfigSLZ
    lookup_field = "id"
    filter_backends = [SerializerFilterBackend, SearchFilter, OrderingFilter]
    filter_serializer = serializers.PluginConfigFilterSLZ
    search_fields = ["name"]
    ordering_fields = ["name", "-name", "type", "-type", "updated_time", "-updated_time"]

    def get_queryset(self):
        return PluginConfig.objects.prefetch_related("type").filter(api=self.request.gateway)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        request = self.request

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.PLUGIN.value,
            op_object_id=serializer.instance.id,
            op_object=serializer.instance.name,
            comment=_("创建插件"),
        )

    def perform_destroy(self, instance):
        if instance.pluginbinding_set.exists():
            raise error_codes.INVALID_ARGUMENT.format(_("插件已绑定环境或资源，请解除绑定后再删除插件。"))

        super().perform_destroy(instance)
        request = self.request

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.PLUGIN.value,
            op_object_id=instance.id,
            op_object=instance.name,
            comment=_("删除插件"),
        )

    def perform_update(self, serializer):
        super().perform_update(serializer)
        request = self.request

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.PLUGIN.value,
            op_object_id=serializer.instance.id,
            op_object=serializer.instance.name,
            comment=_("更新插件"),
        )


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        operation_description="list the available plugin types",
    ),
)
class PluginTypeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.PluginTypeSLZ
    renderer_classes = [ResponseRender, BrowsableAPIRenderer]

    def get_queryset(self):
        """默认展示所有公开插件；针对非公开插件，假如当前请求的网关已启用插件，则展示"""
        related_type_ids = PluginConfig.objects.filter(api=self.request.gateway, type__isnull=False).values_list(
            "type__id", flat=True
        )

        # 大多数情况，related_type_ids 为空，单独处理更简洁，效率更高
        if not related_type_ids:
            return PluginType.objects.filter(is_public=True).order_by("code")

        return PluginType.objects.filter(Q(is_public=True) | Q(id__in=related_type_ids)).order_by("code")


@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        tags=["Plugin"],
        operation_description="retrieve the plugin form data by plugin type",
    ),
)
class PluginFormViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.PluginFormSLZ
    renderer_classes = [ResponseRender, BrowsableAPIRenderer]

    def get_object(self):
        plugin_type = get_object_or_404(
            PluginType.objects.all(),
            pk=int(self.kwargs["type_id"]),
        )

        form = plugin_type.pluginform_set.with_language().first()
        if form:
            return form

        return PluginForm.fake_object(plugin_type)
