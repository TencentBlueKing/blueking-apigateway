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
from typing import Dict

from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginStyleEnum, PluginTypeScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm, PluginType
from apigateway.common.audit.shortcuts import record_audit_log
from apigateway.common.error_codes import error_codes
from apigateway.common.release.publish import trigger_gateway_publish
from apigateway.common.renderers import BkStandardApiJSONRenderer
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import Resource, Stage
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    PluginBindingListOutputSLZ,
    PluginConfigCreateInputSLZ,
    PluginConfigRetrieveUpdateInputSLZ,
    PluginFormOutputSLZ,
    PluginTypeOutputSLZ,
    PluginTypeQueryInputSLZ,
    ScopePluginConfigListOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=PluginTypeQueryInputSLZ,
        responses={status.HTTP_200_OK: PluginTypeOutputSLZ(many=True)},
        tags=["WebAPI.Plugin"],
        operation_description="list the available plugin types",
    ),
)
class PluginTypeListApi(generics.ListAPIView):
    serializer_class = PluginTypeOutputSLZ

    def get_serializer_context(self):
        # 需要返回描述，描述在 plugin_form 中
        plugin_type_notes = {i["type_id"]: i["notes"] for i in PluginForm.objects.values("type_id", "notes")}

        # 需要返回每个 pluginType 是否已经被当前资源绑定
        current_scope_type = self.request.query_params.get("scope_type")
        current_scope_id = self.request.query_params.get("scope_id")
        type_is_bound_to_current_scope: Dict[int, bool] = {}

        # 需要返回每个 pluginType 对应绑定的环境数量/资源数量
        type_related_scope_count = {}
        gateway = self.request.gateway
        for binding in PluginBinding.objects.filter(gateway=gateway).prefetch_related("config", "config__type").all():
            key = binding.config.type.id
            if key not in type_related_scope_count:
                type_related_scope_count[key] = {
                    "stage": 0,
                    "resource": 0,
                }

            # all
            scope_type = binding.scope_type
            count = type_related_scope_count[key].get(scope_type, 0)
            type_related_scope_count[key][scope_type] = count + 1

            # is_bound
            if current_scope_type == scope_type and current_scope_id == binding.scope_id:
                type_is_bound_to_current_scope[key] = True

        return {
            "plugin_type_notes": plugin_type_notes,
            "type_related_scope_count": type_related_scope_count,
            "type_is_bound_to_current_scope": type_is_bound_to_current_scope,
        }

    def get_queryset(self):
        """默认展示所有公开插件；不展示非公开插件"""

        slz = PluginTypeQueryInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        scope_type = data.get("scope_type")
        # scope_id = data.get("scope_id")

        scope = (
            PluginTypeScopeEnum.STAGE.value
            if scope_type == PluginBindingScopeEnum.STAGE.value
            else PluginTypeScopeEnum.RESOURCE.value
        )
        queryset = PluginType.objects.filter(is_public=True).filter(
            Q(scope=PluginTypeScopeEnum.STAGE_AND_RESOURCE.value) | Q(scope=scope)
        )

        # 支持 keyword=abc 搜索
        keyword = data.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))

        return queryset.order_by("code")


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: PluginFormOutputSLZ()},
        tags=["WebAPI.Plugin"],
        operation_description="retrieve the plugin form data by plugin type",
    ),
)
class PluginFormRetrieveApi(generics.RetrieveAPIView):
    serializer_class = PluginFormOutputSLZ
    renderer_classes = [BkStandardApiJSONRenderer]

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
            if not Stage.objects.filter(gateway=gateway, id=scope_id).exists():
                raise error_codes.INVALID_ARGUMENT.format(f"scope_type {scope_type}, scope_id {scope_id} is invalid")
        elif scope_type == "resource":
            if not Resource.objects.filter(gateway=gateway, id=scope_id).exists():
                raise error_codes.INVALID_ARGUMENT.format(f"scope_type {scope_type}, scope_id {scope_id} is invalid")
        else:
            raise error_codes.INVALID_ARGUMENT.format(f"scope_type {scope_type} is invalid")


class PluginTypeCodeValidationMixin:
    def validate_code(self, type_id=0):
        code = self.kwargs["code"]

        plugin_type = PluginType.objects.filter(code=code).first()
        if not plugin_type:
            raise error_codes.INVALID_ARGUMENT.format(f"code {code} is invalid")

        if type_id and plugin_type != type_id:
            raise error_codes.INVALID_ARGUMENT.format(
                f"code {code} in query_string is not matched the type_id={type_id.id}(code={type_id.code}) in body"
            )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        request_body=PluginConfigCreateInputSLZ,
        tags=["WebAPI.Plugin"],
        operation_description="create the plugin config, and bind to the scope_type/scope_id",
    ),
)
class PluginConfigCreateApi(generics.CreateAPIView, ScopeValidationMixin, PluginTypeCodeValidationMixin):
    serializer_class = PluginConfigCreateInputSLZ
    renderer_classes = [BkStandardApiJSONRenderer]

    def get_queryset(self):
        return PluginConfig.objects.prefetch_related("type").filter(gateway=self.request.gateway)

    @transaction.atomic
    def perform_create(self, serializer):
        self.validate_scope()
        self.validate_code(type_id=serializer.validated_data["type_id"])
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]

        duplicated = PluginBinding.objects.filter(
            gateway=self.request.gateway,
            scope_type=scope_type,
            scope_id=scope_id,
            config__type__code=self.kwargs["code"],
        ).exists()
        if duplicated:
            raise error_codes.FAILED_PRECONDITION.format(
                f"{scope_type} {scope_id} already bind to {self.kwargs['code']}"
            )

        super().perform_create(serializer)

        # binding
        PluginBinding(
            gateway=self.request.gateway,
            scope_type=scope_type,
            scope_id=scope_id,
            config=serializer.instance,
        ).save()

        request = self.request
        # if scope_type is stage, should publish
        if scope_type == PluginBindingScopeEnum.STAGE.value:
            # 触发环境发布
            trigger_gateway_publish(
                PublishSourceEnum.PLUGIN_BIND,
                request.user.username,
                request.gateway.id,
                scope_id,
                is_sync=False,
            )

        # audit
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
        responses={status.HTTP_204_NO_CONTENT: PluginConfigRetrieveUpdateInputSLZ()},
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: PluginConfigRetrieveUpdateInputSLZ()},
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Plugin"],
    ),
)
class PluginConfigRetrieveUpdateDestroyApi(
    generics.RetrieveUpdateDestroyAPIView, ScopeValidationMixin, PluginTypeCodeValidationMixin
):
    serializer_class = PluginConfigRetrieveUpdateInputSLZ
    renderer_classes = [BkStandardApiJSONRenderer]

    lookup_field = "id"

    def get_queryset(self):
        return PluginConfig.objects.prefetch_related("type").filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        self.validate_scope()
        self.validate_code()
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        self.validate_scope()
        self.validate_code(type_id=serializer.validated_data["type_id"])

        super().perform_update(serializer)
        request = self.request

        # if scope_type is stage, should publish
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]
        if scope_type == PluginBindingScopeEnum.STAGE.value:
            # 触发环境发布
            trigger_gateway_publish(
                PublishSourceEnum.PLUGIN_UPDATE,
                request.user.username,
                request.gateway.id,
                scope_id,
                is_sync=False,
            )

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

    @transaction.atomic
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

        # if scope_type is stage, should publish
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]
        if scope_type == PluginBindingScopeEnum.STAGE.value:
            # 触发环境发布
            trigger_gateway_publish(
                PublishSourceEnum.PLUGIN_UPDATE,
                request.user.username,
                request.gateway.id,
                scope_id,
                is_sync=False,
            )

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


class PluginBindingListApi(generics.ListAPIView, PluginTypeCodeValidationMixin):
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

        stages = Stage.objects.filter(gateway=gateway, id__in=stage_ids).values("id", "name")
        resources = Resource.objects.filter(gateway=gateway, id__in=resource_ids).values("id", "name")
        data = {
            "stages": stages,
            "resources": resources,
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
                "code": binding.config.type.code,
                "name": binding.config.type.name,
                "config": binding.get_config(),
                "config_id": binding.config.id,
            }
            for binding in bindings
        ]

        serializer = ScopePluginConfigListOutputSLZ(data, many=True)
        return OKJsonResponse(data=serializer.data)
