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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.plugin.binding import serializers
from apigateway.apps.plugin.binding.plan import PluginBindingPlan
from apigateway.apps.plugin.binding.validator import PluginBindingValidator
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.core.signals import gateway_update_signal
from apigateway.utils.filterset import SerializerFilterBackend
from apigateway.utils.responses import ResponseRender


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        tags=["PluginBinding"],
        query_serializer=serializers.PluginBindingFilterSLZ(),
        operation_description="list the plugin binding details",
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        tags=["PluginBinding"],
        operation_description="get the specified plugin binding details",
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        tags=["PluginBinding"],
        operation_description="delete the specified plugin binding",
    ),
)
class PluginBindingViewSet(viewsets.ModelViewSet):
    renderer_classes = [ResponseRender, BrowsableAPIRenderer]
    serializer_class = serializers.PluginBindingSLZ
    filter_backends = [SerializerFilterBackend, OrderingFilter]
    filter_serializer = serializers.PluginBindingFilterSLZ
    ordering_fields = ["scope_id"]

    def get_queryset(self):
        return PluginBinding.objects.filter(gateway=self.request.gateway)

    def perform_destroy(self, instance):
        record_audit_log(
            username=self.request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=self.request.gateway.id,
            op_object_type=OpObjectTypeEnum.PLUGIN.value,
            op_object_id=instance.config.pk,
            op_object=instance.config.name,
            comment=_("删除插件绑定"),
        )

        return super().perform_destroy(instance)


class PluginBindingBatchViewSet(viewsets.GenericViewSet):
    renderer_classes = [ResponseRender, BrowsableAPIRenderer]
    serializer_class = serializers.PluginBindingBatchSLZ
    pagination_class = None
    filter_backends = [SerializerFilterBackend, OrderingFilter]
    filter_serializer = serializers.PluginBindingFilterSLZ
    ordering_fields = ["scope_id"]

    def get_queryset(self):
        return PluginBinding.objects.filter(gateway=self.request.gateway)

    def _get_plugin_config(self):
        return get_object_or_404(PluginConfig, gateway=self.request.gateway, pk=self.kwargs["config_id"])

    def _execute_plan(self, plan: PluginBindingPlan):
        plugin = plan.config
        record_audit_log(
            username=self.request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=self.request.gateway.id,
            op_object_type=OpObjectTypeEnum.PLUGIN.value,
            op_object_id=plugin.pk,
            op_object=plugin.name,
            comment=_("更新插件绑定"),
        )

        if plan.binds:
            PluginBinding.objects.bulk_update_or_create(plan.binds, plan.update_fields)
            # 批量创建、更新，未触发更新信号，因此主动触发信号，以便及时更新到网关服务
            gateway_update_signal.send(PluginBinding, gateway_id=plugin.gateway.pk)

        if plan.unbinds:
            PluginBinding.objects.bulk_delete(plan.unbinds)

    @transaction.atomic
    def _handle(self, request, plan_update_fun, validate_binding_scopes=False, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = plan_update_fun(
            queryset=self.get_queryset(),
            updated_by=request.user.username,
            scope_type=serializer.validated_data["scope_type"],
            scope_ids=serializer.validated_data["scope_ids"],
        )

        # 插件机制同时支持访问策略、插件配置两种方案。
        # 发布到 apisix 网关时，若同一环境、资源绑定同一类型访问策略、插件配置，插件配置优先；
        # 为避免数据覆盖的风险，管理端绑定插件配置时，要求不能存在绑定到同一类型的访问策略。
        # 管理员为网关启用插件配置时，应尽快将网关的访问策略全部迁移到插件配置。
        # TODO: 待访问策略全部迁移到插件配置，去除此校验
        if validate_binding_scopes:
            validator = PluginBindingValidator(
                gateway=self.request.gateway,
                scope_type=PluginBindingScopeEnum(serializer.validated_data["scope_type"]),
                scope_ids=serializer.validated_data["scope_ids"],
                plugin_type_code=plan.config.type.code,
            )
            validator.validate()

        if not serializer.validated_data.get("dry_run"):
            self._execute_plan(plan)

        serializer = serializers.PluginBindingBatchResponseSLZ(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["PluginBinding"],
        request_body=serializers.PluginBindingBatchSLZ(),
        responses={status.HTTP_200_OK: serializers.PluginBindingBatchResponseSLZ()},
        operation_description="bind the plugin to the specified scopes",
    )
    def bind(self, request, *args, **kwargs):
        """绑定插件到环境、资源或服务，覆盖原本对象的同类型插件"""
        plan = PluginBindingPlan(config=self._get_plugin_config())
        return self._handle(request, plan.update_for_bind, validate_binding_scopes=True, *args, **kwargs)

    @swagger_auto_schema(
        tags=["PluginBinding"],
        request_body=serializers.PluginBindingBatchSLZ(),
        responses={status.HTTP_200_OK: serializers.PluginBindingBatchResponseSLZ()},
        operation_description="unbind the plugin from the specified scopes",
    )
    def unbind(self, request, *args, **kwargs):
        """解绑环境、资源或服务的插件，仅处理指定的插件"""
        plan = PluginBindingPlan(config=self._get_plugin_config())
        return self._handle(request, plan.update_for_unbind, *args, **kwargs)

    @swagger_auto_schema(
        tags=["PluginBinding"],
        query_serializer=serializers.PluginBindingFilterSLZ(),
        responses={status.HTTP_200_OK: serializers.PluginBindingBatchResponseSLZ()},
        operation_description="list all the related plugin bindings",
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        response_slz = serializers.PluginBindingBatchResponseSLZ(
            {
                "binds": queryset.filter(config=self._get_plugin_config()),
            }
        )
        return Response(response_slz.data)
