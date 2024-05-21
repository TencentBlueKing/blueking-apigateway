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
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_app_binding import GatewayAppBindingHandler
from apigateway.biz.iam import IAMAuthHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.error_codes import error_codes
from apigateway.common.release.publish import trigger_gateway_publish
from apigateway.core.constants import GatewayStatusEnum, PublishSourceEnum
from apigateway.core.models import Gateway
from apigateway.iam.constants import GATEWAY_DEFAULT_ROLES, ActionEnum, UserRoleEnum
from apigateway.iam.handlers.gateway_member import GatewayMemberHandler
from apigateway.iam.handlers.user_group import IAMUserGroupHandler
from apigateway.iam.models import IAMGradeManager
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    GatewayCreateInputSLZ,
    GatewayFeatureFlagsOutputSLZ,
    GatewayListInputSLZ,
    GatewayListOutputSLZ,
    GatewayRetrieveOutputSLZ,
    GatewayRoleInputSLZ,
    GatewayRoleMembersInputSLZ,
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
    def list(self, request, *args, **kwargs):
        # 获取用户有权限的网关列表，后续切换到 IAM
        gateways = GatewayHandler().list_gateways_by_user(request.user.username)
        gateway_ids = [gateway.id for gateway in gateways]

        slz = GatewayListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = self._filter_list_queryset(
            gateway_ids,
            slz.validated_data.get("keyword"),
            slz.validated_data["order_by"],
        )
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
    method_permission = {
        "get": ActionEnum.VIEW_GATEWAY.value,
        "put": ActionEnum.MANAGE_GATEWAY.value,
        "patch": ActionEnum.MANAGE_GATEWAY.value,
        "delete": ActionEnum.MANAGE_GATEWAY.value,
    }

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
    method_permission = {
        "put": ActionEnum.MANAGE_GATEWAY.value,
    }

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
    method_permission = {
        "get": ActionEnum.VIEW_GATEWAY.value,
    }

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
        operation_description="获取网关成员列表",
        responses={status.HTTP_200_OK: GatewayRoleMembersInputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="添加网关成员",
        request_body=GatewayRoleMembersInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayRoleMembersListCreateApi(generics.ListCreateAPIView):
    method_permission = {
        "get": ActionEnum.VIEW_MEMBERS.value,
        "post": ActionEnum.MANAGE_MEMBERS.value,
    }

    queryset = Gateway.objects.all()
    lookup_url_kwarg = "gateway_id"

    member_handler = GatewayMemberHandler()
    group_handler = IAMUserGroupHandler()

    def list(self, request, *args, **kwargs):
        instance = self.get_object()

        role_members = []
        for role in GATEWAY_DEFAULT_ROLES:
            exists_usernames = {i["username"] for i in role_members}
            usernames = self.group_handler.fetch_user_group_members(instance.id, role)
            role_members.extend([{"username": i, "role": role.value} for i in usernames if i not in exists_usernames])

        return OKJsonResponse(data=role_members)

    def create(self, request, *args, **kwargs):
        slz = GatewayRoleMembersInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        username = slz.validated_data["username"]
        role = slz.validated_data["role"]

        instance = self.get_object()

        self.member_handler.add_member(instance, UserRoleEnum.get(role), username)

        Auditor.record_gateway_member_op_success(
            op_type=OpTypeEnum.CREATE,
            username=request.user.username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={},
            data_after=slz.validated_data,
        )

        return OKJsonResponse()


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="切换网关成员角色",
        request_body=GatewayRoleInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除网关成员",
        request_body=GatewayRoleInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayRoleMembersUpdateDestroyApi(generics.UpdateAPIView, generics.DestroyAPIView):
    method_permission = {
        "put": ActionEnum.MANAGE_MEMBERS.value,
        "delete": ActionEnum.MANAGE_MEMBERS.value,
    }

    queryset = Gateway.objects.all()
    lookup_url_kwarg = "gateway_id"

    member_handler = GatewayMemberHandler()
    group_handler = IAMUserGroupHandler()

    def update(self, request, *args, **kwargs):
        slz = GatewayRoleInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        instance = self.get_object()

        username = kwargs["username"]
        get_object_or_404(get_user_model(), username=username)
        for role in self.group_handler.get_user_role(instance.id, username):
            self.member_handler.delete_member(instance, role, username)

        role = slz.validated_data["role"]
        self.member_handler.add_member(instance, UserRoleEnum.get(role), username)

        Auditor.record_gateway_member_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={},
            data_after=slz.validated_data,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        slz = GatewayRoleInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        username = kwargs["username"]
        get_object_or_404(get_user_model(), username=username)
        role = slz.validated_data["role"]

        instance = self.get_object()

        self.member_handler.delete_member(instance, UserRoleEnum.get(role), username)

        Auditor.record_gateway_member_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={},
            data_after=slz.validated_data,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取登录用户对应网关的角色",
        responses={status.HTTP_200_OK: GatewayRoleInputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="退出网关角色",
        request_body=GatewayRoleInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayRoleRetrieveDestroyApi(generics.RetrieveAPIView, generics.DestroyAPIView):
    method_permission = {
        "get": ActionEnum.VIEW_GATEWAY.value,
        "delete": ActionEnum.VIEW_GATEWAY.value,
    }

    queryset = Gateway.objects.all()
    lookup_url_kwarg = "gateway_id"

    group_handler = IAMUserGroupHandler()
    member_handler = GatewayMemberHandler()
    auth_handler = IAMAuthHandler()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not IAMGradeManager.objects.filter(gateway=instance).exists():
            role = UserRoleEnum.MANAGER.value if instance.has_permission(request.user.username) else None
            return OKJsonResponse(data={"role": role})

        roles = self.group_handler.get_user_role(instance.id, request.user.username)
        if roles:
            return OKJsonResponse(data={"role": roles[0].value})

        # 特殊用户, 比如超级管理员, 可能会有any权限, 直接返回MANAGER
        policies = self.auth_handler.query_policies(request.user.username, ActionEnum.VIEW_GATEWAY.value)
        if policies and self.auth_handler.is_any_policies(policies):
            return OKJsonResponse(data={"role": UserRoleEnum.MANAGER.value})

        return OKJsonResponse(data={"role": None})

    def destroy(self, request, *args, **kwargs):
        slz = GatewayRoleInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        role = slz.validated_data["role"]

        instance = self.get_object()

        self.member_handler.delete_member(instance, UserRoleEnum.get(role), request.user.username)

        Auditor.record_gateway_member_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={},
            data_after={"username": request.user.username, "role": role},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
