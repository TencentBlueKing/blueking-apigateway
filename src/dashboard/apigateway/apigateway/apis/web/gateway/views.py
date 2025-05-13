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
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_app_binding import GatewayAppBindingHandler
from apigateway.biz.gateway_related_app import GatewayRelatedAppHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.components.paas import create_paas_app, paas_app_module_offline
from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import (
    GatewayKindEnum,
    GatewayStatusEnum,
    ProgrammableGatewayLanguageEnum,
    PublishSourceEnum,
)
from apigateway.core.models import Gateway, Stage
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.user_credentials import get_user_credentials_from_request

from .serializers import (
    GatewayCreateInputSLZ,
    GatewayDevGuidelineOutputSLZ,
    GatewayFeatureFlagsOutputSLZ,
    GatewayListInputSLZ,
    GatewayListOutputSLZ,
    GatewayRetrieveOutputSLZ,
    GatewayUpdateInputSLZ,
    GatewayUpdateStatusInputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表",
        responses={status.HTTP_200_OK: GatewayListOutputSLZ(many=True)},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建网关",
        request_body=GatewayCreateInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayListCreateApi(generics.ListCreateAPIView):
    serializer_class = GatewayListInputSLZ

    def list(self, request, *args, **kwargs):
        # 获取用户有权限的网关列表，后续切换到 IAM
        gateways = GatewayHandler.list_gateways_by_user(request.user.username)
        gateway_ids = [gateway.id for gateway in gateways]

        slz = GatewayListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = self._filter_list_queryset(
            gateway_ids,
            slz.validated_data.get("keyword"),
            slz.validated_data["order_by"],
        )
        kind = slz.validated_data.get("kind")
        if kind in [GatewayKindEnum.PROGRAMMABLE.value, GatewayKindEnum.NORMAL.value]:
            queryset = queryset.filter(kind=kind)

        page = self.paginate_queryset(queryset)
        gateway_ids = [gateway.id for gateway in page]

        output_slz = GatewayListOutputSLZ(
            page,
            many=True,
            context={
                "resource_count": GatewayHandler.get_resource_count(gateway_ids),
                "stages": GatewayHandler.get_stages_with_release_status(gateway_ids),
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids),
            },
        )

        return self.get_paginated_response(output_slz.data)

    def _filter_list_queryset(self, gateway_ids: List[int], keyword: Optional[str], order_by: str):
        queryset = Gateway.objects.filter(id__in=gateway_ids)

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        return queryset.order_by(order_by)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = GatewayCreateInputSLZ(data=request.data, context={"created_by": request.user.username})
        slz.is_valid(raise_exception=True)

        bk_app_codes = slz.validated_data.pop("bk_app_codes", None)

        # if kind is programmable, create paas app
        if slz.validated_data.get("kind") == GatewayKindEnum.PROGRAMMABLE.value:
            git_info = None
            if settings.EDITION == "ee":
                git_info = slz.validated_data.pop("programmable_gateway_git_info", None)
                if not git_info:
                    raise error_codes.INVALID_ARGUMENT.format(_("可编程网关 Git 信息不能为空。"), replace=True)

            ok = create_paas_app(
                slz.validated_data["name"],
                git_info,
                user_credentials=get_user_credentials_from_request(request),
            )
            if not ok:
                raise error_codes.INTERNAL.format(_("创建蓝鲸应用失败。"), replace=True)

        # 1. save gateway
        slz.save(
            status=GatewayStatusEnum.ACTIVE.value,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 2. save related data
        GatewayHandler.save_related_data(
            gateway=slz.instance,
            user_auth_type=UserAuthTypeEnum(settings.DEFAULT_USER_AUTH_TYPE).value,
            # 通过管理端新创建的网关，要求必须使用请求头提供蓝鲸认证数据
            allow_auth_from_params=False,
            # 通过管理端新创建的网关，不需要删除敏感参数
            allow_delete_sensitive_params=False,
            username=request.user.username,
            app_codes_to_binding=bk_app_codes,
        )

        # 3. record audit log
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.CREATE,
            username=request.user.username,
            gateway_id=slz.instance.id,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
            data_before={},
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED, data={"id": slz.instance.id})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定网关的信息",
        responses={status.HTTP_200_OK: GatewayRetrieveOutputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新网关",
        request_body=GatewayUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="更新网关部分信息",
        request_body=GatewayUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除网关",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayRetrieveOutputSLZ
    lookup_url_kwarg = "gateway_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = GatewayRetrieveOutputSLZ(
            instance,
            context={
                "auth_config": GatewayAuthContext().get_auth_config(instance.pk),
                "bk_app_codes": GatewayAppBindingHandler.get_bound_app_codes(instance),
                "related_app_codes": GatewayRelatedAppHandler.get_related_app_codes(request.gateway.id),
            },
        )
        return OKJsonResponse(data=slz.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = GatewayUpdateInputSLZ(instance=instance, data=request.data, partial=partial)
        slz.is_valid(raise_exception=True)

        bk_app_codes = slz.validated_data.pop("bk_app_codes", None)

        slz.save(updated_by=request.user.username)

        if bk_app_codes is not None:
            GatewayAppBindingHandler.update_gateway_app_bindings(instance, bk_app_codes)

        related_app_codes = slz.validated_data.pop("related_app_codes", None)
        if related_app_codes is not None:
            GatewayRelatedAppHandler.update_related_app_codes(request.gateway, related_app_codes)

        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)
        instance_id = instance.id

        # 网关为“停用”状态，才可以删除
        if instance.is_active:
            raise error_codes.FAILED_PRECONDITION.format(_("请先停用网关，然后再删除。"), replace=True)

        GatewayHandler.delete_gateway(instance_id)

        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=instance_id,
            instance_id=instance_id,
            instance_name=instance.name,
            data_before=data_before,
            data_after={},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新网关状态，如启用、停用",
        request_body=GatewayUpdateStatusInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayUpdateStatusApi(generics.UpdateAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayUpdateStatusInputSLZ
    lookup_url_kwarg = "gateway_id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = self.get_serializer(instance=instance, data=request.data)
        slz.is_valid(raise_exception=True)

        is_need_publish = slz.validated_data["status"] is not instance.status

        slz.save(updated_by=request.user.username)

        # 触发网关发布
        if is_need_publish:
            # 由于没有办法知道停用状态(网关停用会变更环境的发布状态)之前的各环境发布状态，则启用会发布所有环境
            source = PublishSourceEnum.GATEWAY_ENABLE if instance.is_active else PublishSourceEnum.GATEWAY_DISABLE
            trigger_gateway_publish(source, request.user.username, instance.id)
            # todo: 编程网关启用需要特殊处理
            if instance.is_programmable and source == PublishSourceEnum.GATEWAY_DISABLE:
                # 编程网关停用时，需要调用paas的module_offline接口下架所有环境
                active_stages = Stage.objects.get_gateway_name_to_active_stage_names([instance]).get(instance.name)
                for stage_name in active_stages:
                    paas_app_module_offline(
                        app_code=request.gateway.name,
                        module="default",
                        env=stage_name,
                        user_credentials=get_user_credentials_from_request(request),
                    )

        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关特性开关",
        responses={status.HTTP_200_OK: GatewayFeatureFlagsOutputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayFeatureFlagsApi(generics.ListAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayFeatureFlagsOutputSLZ
    lookup_url_kwarg = "gateway_id"

    def list(self, request, *args, **kwargs):
        instance = self.get_object()

        feature_flags = GatewayHandler.get_feature_flags(instance.pk)
        slz = self.get_serializer({"feature_flags": feature_flags})

        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定网关的开发指引页面",
        responses={status.HTTP_200_OK: GatewayDevGuidelineOutputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayDevGuidelineRetrieveApi(generics.RetrieveAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayDevGuidelineOutputSLZ
    lookup_url_kwarg = "gateway_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.is_programmable:
            raise error_codes.FAILED_PRECONDITION.format(_("当前网关类型不支持开发指引。"), replace=True)

        language = instance.extra_info.get("language")
        dev_guideline_url = ""
        if language == ProgrammableGatewayLanguageEnum.PYTHON.value:
            dev_guideline_url = settings.PROGRAMMABLE_GATEWAY_DEV_GUIDELINE_PYTHON_URL
        elif language == ProgrammableGatewayLanguageEnum.GO.value:
            dev_guideline_url = settings.PROGRAMMABLE_GATEWAY_DEV_GUIDELINE_GO_URL

        template_name = f"dev_guideline/{get_current_language_code()}/programmable_gateway.md"

        repo_url = instance.extra_info.get("repository")

        slz = GatewayDevGuidelineOutputSLZ(
            {
                "content": render_to_string(
                    template_name,
                    context={
                        "edition": settings.EDITION,
                        "bk_api_url_tmple": settings.BK_API_URL_TEMPLATE,
                        "language": language,
                        "repo_url": repo_url,
                        "dev_guideline_url": dev_guideline_url,
                        "project_name": instance.name,
                        "init_admin": request.user.username,
                    },
                )
            }
        )
        return OKJsonResponse(data=slz.data)
