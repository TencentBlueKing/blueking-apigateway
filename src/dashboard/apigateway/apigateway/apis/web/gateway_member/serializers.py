#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
