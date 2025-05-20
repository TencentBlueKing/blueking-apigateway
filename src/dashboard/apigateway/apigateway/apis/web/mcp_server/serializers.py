#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

from typing import Any, Dict

from rest_framework import serializers

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer


class MCPServerCreateInputSLZ(serializers.ModelSerializer):
    stage_id = serializers.IntegerField(help_text="Stage ID")

    class Meta:
        model = MCPServer
        fields = ("name", "description", "stage_id", "is_public", "labels", "resource_ids")
        lookup_field = "id"
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerCreateInputSLZ"

    def create(self, validated_data):
        validated_data["gateway_id"] = self.context["gateway_id"]
        validated_data["created_by"] = self.context["created_by"]
        validated_data["status"] = self.context["status"]
        return super().create(validated_data)


class MCPServerBaseOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")

    is_public = serializers.BooleanField(read_only=True, help_text="MCPServer 是否公开")

    labels = serializers.ListField(read_only=True, help_text="MCPServer 标签")
    resource_ids = serializers.ListField(read_only=True, help_text="MCPServer 资源 ID")

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")

    status = serializers.ChoiceField(
        read_only=True, help_text="MCPServer 状态", choices=MCPServerStatusEnum.get_choices()
    )

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")

    def get_stage(self, obj) -> Dict[str, Any]:
        return self.context["stages"][obj.stage.id]


class MCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerListOutputSLZ"


class MCPServerRetrieveOutputSLZ(MCPServerBaseOutputSLZ):
    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRetrieveOutputSLZ"


class MCPServerUpdateInputSLZ(serializers.ModelSerializer):
    labels = serializers.ListField(child=serializers.CharField(), required=False, help_text="MCPServer 标签列表")
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, help_text="MCPServer 资源 ID 列表"
    )

    class Meta:
        model = MCPServer
        fields = ("description", "is_public", "labels", "resource_ids")
        lookup_field = "id"
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateInputSLZ"


class MCPServerUpdateStatusInputSLZ(serializers.ModelSerializer):
    class Meta:
        model = MCPServer
        fields = ("status",)
        lookup_field = "id"
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateStatusInputSLZ"


class MCPServerUpdateLabelsInputSLZ(serializers.ModelSerializer):
    labels = serializers.ListField(child=serializers.CharField(), required=True, help_text="MCPServer 标签列表")

    class Meta:
        model = MCPServer
        fields = ("labels",)
        lookup_field = "id"
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateLabelsInputSLZ"
