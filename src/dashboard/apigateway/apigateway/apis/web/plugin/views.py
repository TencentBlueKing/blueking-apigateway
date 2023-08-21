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
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.plugin.constants import PluginStyleEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm, PluginType
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Resource, Stage
from apigateway.utils.responses import OKJsonResponse, ResponseRender

from .serializers import (
    PluginBindingListOutputSLZ,
    PluginConfigCreateInputSLZ,
    PluginConfigRetrieveUpdateInputSLZ,
    PluginFormSLZ,
    PluginTypeSLZ,
    ScopePluginConfigListOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
        operation_description="list the available plugin types",
    ),
)
class PluginTypeListApi(generics.ListAPIView):
    serializer_class = PluginTypeSLZ
    renderer_classes = [ResponseRender]

    def get_queryset(self):
        """默认展示所有公开插件；针对非公开插件，假如当前请求的网关已启用插件，则展示"""
        related_type_ids = PluginConfig.objects.filter(gateway=self.request.gateway, type__isnull=False).values_list(
            "type__id", flat=True
        )

        # FIXME: 需要区分 stage 和 resource 的插件类型

        # 大多数情况，related_type_ids 为空，单独处理更简洁，效率更高
        if not related_type_ids:
            return PluginType.objects.filter(is_public=True).order_by("code")

        return PluginType.objects.filter(Q(is_public=True) | Q(id__in=related_type_ids)).order_by("code")


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
        operation_description="retrieve the plugin form data by plugin type",
    ),
)
class PluginFormRetrieveApi(generics.RetrieveAPIView):
    serializer_class = PluginFormSLZ
    renderer_classes = [ResponseRender]

    def get_object(self):
        plugin_type = get_object_or_404(
            PluginType.objects.all(),
            code=self.kwargs["code"],
        )

        form = plugin_type.pluginform_set.with_language().first()
        if form:
            return form

        return PluginForm(
            pk=None,
            language="",
            type=plugin_type,
            notes="",
            style=PluginStyleEnum.RAW.value,
            default_value="",
            config={},
        )


class ScopeValidationMixin:
    def validate_scope(self):
        gateway = self.request.gateway
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]

        if scope_type == "stage":
            if not Stage.objects.filter(api=gateway, id=scope_id).exists():
                raise error_codes.INVALID_ARGUMENT.format(f"scope_type {scope_type}, scope_id {scope_id} is invalid")
        elif scope_type == "resource":
            if not Resource.objects.filter(api=gateway, id=scope_id).exists():
                raise error_codes.INVALID_ARGUMENT.format(f"scope_type {scope_type}, scope_id {scope_id} is invalid")
        else:
            raise error_codes.INVALID_ARGUMENT.format(f"scope_type {scope_type} is invalid")


class PluginTypeCodeValidationMixin:
    def validate_code(self):
        code = self.kwargs["code"]
        if not PluginType.objects.filter(code=code).exists():
            raise error_codes.INVALID_ARGUMENT.format(f"code {code} is invalid")


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
        operation_description="create the plugin config, and bind to the scope_type/scope_id",
    ),
)
class PluginConfigCreateApi(generics.CreateAPIView, ScopeValidationMixin, PluginTypeCodeValidationMixin):
    serializer_class = PluginConfigCreateInputSLZ
    renderer_classes = [ResponseRender]

    def get_queryset(self):
        return PluginConfig.objects.prefetch_related("type").filter(gateway=self.request.gateway)

    def perform_create(self, serializer):
        self.validate_scope()
        self.validate_code()
        super().perform_create(serializer)

        # binding
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]
        PluginBinding(
            gateway=self.request.gateway,
            scope_type=scope_type,
            scope_id=scope_id,
            config=serializer.instance,
        ).save()

        # audit
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


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Plugin"],
    ),
)
class PluginConfigRetrieveUpdateDestroyApi(
    generics.RetrieveUpdateDestroyAPIView, ScopeValidationMixin, PluginTypeCodeValidationMixin
):
    serializer_class = PluginConfigRetrieveUpdateInputSLZ
    renderer_classes = [ResponseRender]
    lookup_field = "id"

    def get_queryset(self):
        return PluginConfig.objects.prefetch_related("type").filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        self.validate_scope()
        self.validate_code()
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        self.validate_scope()
        self.validate_code()
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

    def perform_destroy(self, instance):
        self.validate_scope()
        self.validate_code()
        # unbind
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]
        PluginBinding.objects.filter(
            gateway=self.request.gateway, scope_type=scope_type, scope_id=scope_id, config=instance
        ).delete()

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


class PluginBindingRetrieveApi(generics.RetrieveAPIView, PluginTypeCodeValidationMixin):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PluginBindingListOutputSLZ()},
        tags=["WebAPI.Plugin"],
    )
    def get(self, request, *args, **kwargs):
        self.validate_code()

        gateway = request.gateway
        code = self.kwargs["code"]

        bindings = PluginBinding.objects.filter(
            gateway=gateway,
            config__type__code=code,
        )
        stage_ids = []
        resource_ids = []
        for binding in bindings:
            if binding.scope_type == "stage":
                stage_ids.append(binding.scope_id)
            elif binding.scope_type == "resource":
                resource_ids.append(binding.scope_id)

        stage_names = Stage.objects.filter(api=gateway, id__in=stage_ids).values_list("name", flat=True)
        resource_names = Resource.objects.filter(api=gateway, id__in=resource_ids).values_list("name", flat=True)
        data = {
            "stages": stage_names,
            "resources": resource_names,
        }

        serializer = PluginBindingListOutputSLZ(data)
        return OKJsonResponse(data=serializer.data)


class ScopePluginConfigListApi(generics.ListAPIView, ScopeValidationMixin):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ScopePluginConfigListOutputSLZ(many=True)},
        tags=["WebAPI.Plugin"],
    )
    def get(self, request, *args, **kwargs):
        self.validate_scope()

        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]

        bindings = PluginBinding.objects.filter(
            gateway=request.gateway,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        data = [
            {
                "name": binding.config.type.name,
                "config": binding.get_config(),
            }
            for binding in bindings
        ]

        serializer = ScopePluginConfigListOutputSLZ(data, many=True)
        return OKJsonResponse(data=serializer.data)
