from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apigateway.apps.rbac.constants import GatewayRoleEnum


class GatewayMemberOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="成员 ID")
    username = serializers.CharField(read_only=True, help_text="用户名")
    role = serializers.ChoiceField(
        choices=GatewayRoleEnum.get_choices(),
        read_only=True,
        help_text="成员角色",
    )
    created_time = serializers.DateTimeField(read_only=True, help_text="创建时间")
    updated_time = serializers.DateTimeField(read_only=True, help_text="更新时间")
    created_by = serializers.CharField(read_only=True, help_text="创建人")
    updated_by = serializers.CharField(read_only=True, help_text="更新人")


class GatewayMemberCreateListSLZ(serializers.ListSerializer):
    def validate(self, attrs):
        usernames = [item["username"] for item in attrs]
        if len(usernames) != len(set(usernames)):
            raise serializers.ValidationError(_("同一用户不能重复提交。"))
        return attrs


class GatewayMemberCreateInputSLZ(serializers.Serializer):
    username = serializers.CharField(max_length=64, allow_blank=False, help_text="用户名")
    role = serializers.ChoiceField(choices=GatewayRoleEnum.get_choices(), help_text="成员角色")

    class Meta:
        list_serializer_class = GatewayMemberCreateListSLZ
        ref_name = "apigateway.apis.web.gateway_member.serializers.GatewayMemberCreateInputSLZ"


class GatewayMemberRoleUpdateInputSLZ(serializers.Serializer):
    role = serializers.ChoiceField(choices=GatewayRoleEnum.get_choices(), help_text="成员角色")

    class Meta:
        ref_name = "apigateway.apis.web.gateway_member.serializers.GatewayMemberRoleUpdateInputSLZ"


class GatewayMemberBatchCreateOutputSLZ(serializers.Serializer):
    created = GatewayMemberOutputSLZ(many=True, read_only=True)
    skipped = GatewayMemberOutputSLZ(many=True, read_only=True)

    class Meta:
        ref_name = "apigateway.apis.web.gateway_member.serializers.GatewayMemberBatchCreateOutputSLZ"
