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
from typing import Any, Dict, Union

from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.plugin.constants import (
    PluginBindingScopeEnum,
    PluginBindingSourceEnum,
    PluginStyleEnum,
    PluginTypeScopeEnum,
)
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm, PluginType
from apigateway.biz.audit import Auditor
from apigateway.common.error_codes import error_codes
from apigateway.common.release.publish import trigger_gateway_publish
from apigateway.common.renderers import BkStandardApiJSONRenderer
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import Resource, Stage
from apigateway.utils.django import get_model_dict
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
        operation_description="获取某个环境或资源下，可配置的插件列表; 需要指定 scope_type 和 scope_id; 可以传递 keyword 进行搜索",
    ),
)
class PluginTypeListApi(generics.ListAPIView):
    serializer_class = PluginTypeOutputSLZ

    def get_serializer_context(self):
        # 需要返回描述，描述在 plugin_form 中
        if get_language() != "zh-cn":
            plugin_type_notes = {
                i["type_id"]: i["notes"] for i in PluginForm.objects.filter(language="en").values("type_id", "notes")
            }
        else:
            plugin_type_notes = {
                i["type_id"]: i["notes"] for i in PluginForm.objects.exclude(language="en").values("type_id", "notes")
            }

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
        operation_description="获取插件类型对应的动态表单",
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


class PluginConfigBindingPostModificationMixin:
    request: Any

    def post_modification(
        self,
        source: PublishSourceEnum,
        op_type: OpTypeEnum,
        scope_type: str,
        scope_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
    ):
        # if scope_type is stage, should publish
        if scope_type == PluginBindingScopeEnum.STAGE.value:
            # 触发环境发布
            trigger_gateway_publish(source, self.request.user.username, self.request.gateway.id, scope_id)
        elif scope_type == PluginBindingScopeEnum.RESOURCE.value:
            # update the resource updated_time
            Resource.objects.get(id=scope_id).save()

        Auditor.record_plugin_op_success(
            op_type=op_type,
            username=self.request.user.username,
            gateway_id=self.request.gateway.id,
            instance_id=instance_id,
            instance_name=instance_name,
            data_before=data_before,
            data_after=data_after,
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        request_body=PluginConfigCreateInputSLZ,
        tags=["WebAPI.Plugin"],
        operation_description="创建一个插件，并且绑定到对应的 scope_type + scope_id",
    ),
)
class PluginConfigCreateApi(
    generics.CreateAPIView,
    ScopeValidationMixin,
    PluginTypeCodeValidationMixin,
    PluginConfigBindingPostModificationMixin,
):
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
            source=PluginBindingSourceEnum.USER_CREATE.value,
            config=serializer.instance,
        ).save()

        self.post_modification(
            source=PublishSourceEnum.PLUGIN_BIND,
            op_type=OpTypeEnum.CREATE,
            scope_type=scope_type,
            scope_id=scope_id,
            instance_id=serializer.instance.id,
            instance_name=serializer.instance.name,
            data_before={},
            data_after=get_model_dict(serializer.instance),
        )

@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: PluginConfigRetrieveUpdateInputSLZ()},
        operation_description="获取插件的配置",
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: PluginConfigRetrieveUpdateInputSLZ()},
        operation_description="更新插件的配置",
        tags=["WebAPI.Plugin"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        operation_description="删除插件的配置",
        tags=["WebAPI.Plugin"],
    ),
)
class PluginConfigRetrieveUpdateDestroyApi(
    generics.RetrieveUpdateDestroyAPIView,
    ScopeValidationMixin,
    PluginTypeCodeValidationMixin,
    PluginConfigBindingPostModificationMixin,
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

        data_before = get_model_dict(serializer.instance)

        super().perform_update(serializer)

        # if scope_type is stage, should publish
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]
        self.post_modification(
            source=PublishSourceEnum.PLUGIN_UPDATE,
            op_type=OpTypeEnum.MODIFY,
            scope_type=scope_type,
            scope_id=scope_id,
            instance_id=serializer.instance.id,
            instance_name=serializer.instance.name,
            data_before=data_before,
            data_after=get_model_dict(serializer.instance),
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

        instance_id = instance.id
        instance_name = instance.name

        data_before = get_model_dict(instance)

        super().perform_destroy(instance)

        # if scope_type is stage, should publish
        scope_type = self.kwargs["scope_type"]
        scope_id = self.kwargs["scope_id"]
        self.post_modification(
            source=PublishSourceEnum.PLUGIN_UNBIND,
            op_type=OpTypeEnum.DELETE,
            scope_type=scope_type,
            scope_id=scope_id,
            instance_id=instance_id,
            instance_name=instance_name,
            data_before=data_before,
            data_after={},
        )


class PluginBindingListApi(generics.ListAPIView, PluginTypeCodeValidationMixin):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PluginBindingListOutputSLZ()},
        operation_description="获取某个插件绑定的环境列表和资源列表",
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
    def get_serializer_context(self):
        # 需要返回每个 pluginType 对应绑定的环境数量/资源数量
        type_related_scope_count = {}
        gateway = self.request.gateway
        for binding in PluginBinding.objects.filter(gateway=gateway).prefetch_related("config", "config__type").all():
            key = binding.config.type.code
            if key not in type_related_scope_count:
                type_related_scope_count[key] = {
                    "stage": 0,
                    "resource": 0,
                }

            # all
            scope_type = binding.scope_type
            count = type_related_scope_count[key].get(scope_type, 0)
            type_related_scope_count[key][scope_type] = count + 1

        return {
            "type_related_scope_count": type_related_scope_count,
        }

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ScopePluginConfigListOutputSLZ(many=True)},
        operation_description="获取某个环境或资源绑定的插件列表 (插件类型 + 插件配置)",
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

        serializer = ScopePluginConfigListOutputSLZ(data, many=True, context=self.get_serializer_context())
        return OKJsonResponse(data=serializer.data)
