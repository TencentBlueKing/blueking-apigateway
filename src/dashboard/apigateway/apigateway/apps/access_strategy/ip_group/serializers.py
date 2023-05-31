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
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.access_strategy.models import IPGroup
from apigateway.common.constants import IP_OR_SEGMENT_PATTERN
from apigateway.common.fields import CurrentGatewayDefault


class IPGroupQuerySLZ(serializers.Serializer):
    query = serializers.CharField(allow_blank=True)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class IPGroupSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    ips = serializers.CharField(label="IP列表", source="_ips", allow_blank=True)

    class Meta:
        model = IPGroup
        fields = (
            "id",
            "api",
            "name",
            "ips",
            "comment",
            "created_by",
            "created_time",
            "updated_time",
        )
        read_only_fields = ("created_by", "created_time", "updated_time")
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=IPGroup.objects.all(),
                fields=("api", "name"),
                message="网关下IP分组名称已经存在",
            )
        ]

    def validate_ips(self, value):
        if not value:
            return ""

        # split with \n\r, then ignore blank line and `# comment`
        lines = [line.strip() for line in value.splitlines()]
        invalid_ips = [
            line for line in lines if line and (not line.startswith("#")) and (not IP_OR_SEGMENT_PATTERN.match(line))
        ]
        if invalid_ips:
            raise serializers.ValidationError(f"包含非IP数据 [{invalid_ips[0]}]")

        return "\n".join(lines)
