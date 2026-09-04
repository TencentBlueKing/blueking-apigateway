from django.db import transaction
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway import add_gateway_members, delete_gateway_member, update_gateway_member_role
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    GatewayMemberBatchCreateOutputSLZ,
    GatewayMemberCreateInputSLZ,
    GatewayMemberOutputSLZ,
    GatewayMemberRoleUpdateInputSLZ,
)


def _serialize_member(member: GatewayMember) -> dict:
    return dict(GatewayMemberOutputSLZ(member).data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关成员列表",
        responses={status.HTTP_200_OK: GatewayMemberOutputSLZ(many=True)},
        tags=["WebAPI.GatewayMember"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="批量添加网关成员",
        request_body=GatewayMemberCreateInputSLZ(many=True),
        responses={status.HTTP_201_CREATED: GatewayMemberBatchCreateOutputSLZ()},
        tags=["WebAPI.GatewayMember"],
    ),
)
class GatewayMemberListCreateApi(generics.GenericAPIView):
    serializer_class = GatewayMemberCreateInputSLZ

    def get(self, request, *args, **kwargs):
        members = GatewayMember.objects.list_gateway_members(request.gateway.id)
        return OKJsonResponse(data=GatewayMemberOutputSLZ(members, many=True).data)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data, many=True, allow_empty=False)
        slz.is_valid(raise_exception=True)

        result = add_gateway_members(
            request.gateway,
            [(item["username"], item["role"]) for item in slz.validated_data],
            request.user.username,
        )
        created = GatewayMemberOutputSLZ(result.created, many=True).data
        skipped = GatewayMemberOutputSLZ(result.skipped, many=True).data

        if result.created:
            Auditor.record_gateway_op_success(
                op_type=OpTypeEnum.CREATE,
                username=request.user.username,
                gateway_id=request.gateway.id,
                instance_id=request.gateway.id,
                instance_name=request.gateway.name,
                data_before={},
                data_after={"members": list(created)},
                comment="添加网关成员",
            )

        return OKJsonResponse(
            status=status.HTTP_201_CREATED,
            data={
                "created": created,
                "skipped": skipped,
            },
        )


@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="变更网关成员角色",
        request_body=GatewayMemberRoleUpdateInputSLZ,
        responses={status.HTTP_200_OK: GatewayMemberOutputSLZ()},
        tags=["WebAPI.GatewayMember"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="移除网关成员",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.GatewayMember"],
    ),
)
class GatewayMemberUpdateDestroyApi(generics.GenericAPIView):
    serializer_class = GatewayMemberRoleUpdateInputSLZ

    @transaction.atomic
    def patch(self, request, member_id: int, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        result = update_gateway_member_role(
            request.gateway,
            member_id,
            slz.validated_data["role"],
            request.user.username,
        )
        if result.changed:
            Auditor.record_gateway_op_success(
                op_type=OpTypeEnum.MODIFY,
                username=request.user.username,
                gateway_id=request.gateway.id,
                instance_id=request.gateway.id,
                instance_name=request.gateway.name,
                data_before={
                    "member": {
                        "id": result.member.id,
                        "username": result.member.username,
                        "role": result.previous_role,
                    }
                },
                data_after={"member": _serialize_member(result.member)},
                comment="变更网关成员角色",
            )

        return OKJsonResponse(data=GatewayMemberOutputSLZ(result.member).data)

    @transaction.atomic
    def delete(self, request, member_id: int, *args, **kwargs):
        member = delete_gateway_member(request.gateway, member_id)
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=request.gateway.id,
            instance_name=request.gateway.name,
            data_before={"member": _serialize_member(member)},
            data_after={},
            comment="移除网关成员",
        )
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
