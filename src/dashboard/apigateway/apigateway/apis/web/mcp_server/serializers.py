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

import re
from typing import Any, Dict

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.apps.mcp_server.utils import build_mcp_server_url
from apigateway.core.models import Stage

from .utils import get_valid_resource_names


class MCPServerCreateInputSLZ(serializers.ModelSerializer):
    stage_id = serializers.IntegerField(help_text="Stage ID")
    labels = serializers.ListField(child=serializers.CharField(), required=False, help_text="MCPServer 标签列表")
    resource_names = serializers.ListField(
        child=serializers.CharField(), required=True, help_text="MCPServer 资源名称列表"
    )
    name = serializers.CharField(required=True, help_text="MCPServer 名称", max_length=64)

    class Meta:
        model = MCPServer
        fields = ("name", "description", "stage_id", "is_public", "labels", "resource_names")
        lookup_field = "id"
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerCreateInputSLZ"

    def validate(self, attrs):
        # 1.First validate stage_id
        stage_id = attrs.get("stage_id")
        if not stage_id:
            raise serializers.ValidationError(_("stage_id 不能为空/不能为 0"))

        try:
            stage = Stage.objects.get(id=stage_id, gateway=self.context["gateway"])
        except Stage.DoesNotExist:
            raise serializers.ValidationError(_("stage_id 非法，当前网关下无该 stage_id"))

        # 2. Then validate name
        # 2.1 not empty
        name = attrs.get("name")
        if not name:
            raise serializers.ValidationError(_("MCPServer 名称不能为空"))

        # 2.2 format: <gateway_name>-<stage_name>-<name>
        gateway = self.context["gateway"]
        prefix = f"{gateway.name}-{stage.name}-"
        if not name.startswith(prefix):
            raise serializers.ValidationError(_("MCPServer 名称格式错误，前缀应该为 ") + prefix)

        # 2.3 only allow lowercase letters, numbers, and dash, not end with dash
        if not re.match(r"^[a-z0-9-]+$", name):
            raise serializers.ValidationError(_("MCPServer 名称只能包含小写字母、数字和短横线"))
        if name.endswith("-"):
            raise serializers.ValidationError(_("MCPServer 名称不能以短横线结尾"))

        # 2.4 check if name exists
        if MCPServer.objects.filter(name=name).exists():
            raise serializers.ValidationError(_("MCPServer 名称已存在"))

        # 3. validate the resource_names
        resource_names = attrs.get("resource_names")
        if not resource_names:
            raise serializers.ValidationError(_("资源名称列表不能为空"))

        valid_resource_names = get_valid_resource_names(gateway_id=self.context["gateway"].id, stage_id=stage_id)
        for resource_name in resource_names:
            if resource_name not in valid_resource_names:
                raise serializers.ValidationError(
                    _("资源名称列表非法，请检查当前环境发布的最新版本中对应资源名称是否存在")
                    + f"resource_name={resource_name}"
                )

        return attrs

    def create(self, validated_data):
        validated_data["gateway_id"] = self.context["gateway"].id
        validated_data["created_by"] = self.context["created_by"]
        validated_data["status"] = self.context["status"]
        return super().create(validated_data)


class MCPServerBaseOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")

    is_public = serializers.BooleanField(read_only=True, help_text="MCPServer 是否公开")

    labels = serializers.ListField(read_only=True, help_text="MCPServer 标签")
    resource_names = serializers.ListField(read_only=True, help_text="MCPServer 资源名称")

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")

    status = serializers.ChoiceField(
        read_only=True, help_text="MCPServer 状态", choices=MCPServerStatusEnum.get_choices()
    )

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")

    def get_stage(self, obj) -> Dict[str, Any]:
        return self.context["stages"][obj.stage.id]

    def get_url(self, obj) -> str:
        return build_mcp_server_url(obj.name)


class MCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerListOutputSLZ"


class MCPServerRetrieveOutputSLZ(MCPServerBaseOutputSLZ):
    guideline = serializers.SerializerMethodField(help_text="MCPServer 使用指南")

    def get_guideline(self, obj) -> str:
        return self.context["guideline"]

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRetrieveOutputSLZ"


class MCPServerUpdateInputSLZ(serializers.ModelSerializer):
    labels = serializers.ListField(child=serializers.CharField(), required=False, help_text="MCPServer 标签列表")
    resource_names = serializers.ListField(
        child=serializers.CharField(), required=False, help_text="MCPServer 资源名称列表"
    )

    def validate_resource_names(self, resource_names):
        if resource_names is not None:
            if len(resource_names) == 0:
                raise serializers.ValidationError(_("资源名称列表不能为空"))
            valid_resource_names = self.context["valid_resource_names"]

            for resource_name in resource_names:
                if resource_name not in valid_resource_names:
                    raise serializers.ValidationError(
                        _("资源名称列表非法，请检查当前环境发布的最新版本中对应资源名称是否存在")
                        + f"resource_name={resource_name}"
                    )

    class Meta:
        model = MCPServer
        fields = ("description", "is_public", "labels", "resource_names")
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
