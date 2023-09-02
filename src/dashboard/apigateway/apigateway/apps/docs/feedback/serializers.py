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
from django.conf import settings
from rest_framework import serializers

from apigateway.apps.docs.helper import support_helper
from apigateway.common.mixins.serializers import ExtensibleFieldMixin

from .models import Feedback, FeedbackRelatedComponent


class RelatedComponentSLZ(serializers.ModelSerializer):
    class Meta:
        model = FeedbackRelatedComponent
        fields = [
            "board",
            "system_name",
            "component_name",
        ]

    def validate_board(self, value):
        if value not in settings.ESB_BOARD_CONFIGS:
            raise serializers.ValidationError(f"board 值非法: {value}")
        return value


class RelatedAPIGatewaySLZ(serializers.Serializer):
    api_name = serializers.CharField()
    stage_name = serializers.CharField(required=False, allow_blank=True)
    resource_name = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data: dict) -> dict:
        data = super().to_internal_value(data)

        gateway_name = data["api_name"]
        stage_name = data.get("stage_name", "")
        resource_name = data.get("resource_name", "")

        gateway = support_helper.get_gateway_by_name(gateway_name)
        if not gateway:
            raise serializers.ValidationError(
                {
                    "api_name": f"网关[{gateway_name}]不存在",
                }
            )

        resource = {}
        if stage_name and resource_name:
            resource = support_helper.get_released_resource(gateway["id"], stage_name, resource_name)
            if not resource:
                raise serializers.ValidationError(
                    {
                        "resource_name": f"网关[{gateway_name}]的环境[{stage_name}]下，资源[{resource_name}]不存在",
                    }
                )

        return {
            "api_id": gateway["id"],
            "stage_name": stage_name,
            "resource_id": resource.get("id"),
        }


class FeedbackCreateSLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    positive = serializers.BooleanField(help_text="是否有帮助")
    labels = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    related_component = RelatedComponentSLZ(required=False, allow_null=True)
    related_apigateway = RelatedAPIGatewaySLZ(required=False, allow_null=True)

    # TODO:
    # 1. screenshot 是否需要拆分为单独的上传的接口
    # 2. 文件名如何处理冲突，应由后端生成链接地址，链接地址中文件名不能冲突

    class Meta:
        model = Feedback
        fields = [
            "doc_type",
            "labels",
            "link",
            "content",
            "screenshot",
            "positive",
            "related_component",
            "related_apigateway",
        ]

        non_model_fields = ["related_component", "related_apigateway"]
        lookup_field = "id"

    def validate(self, data: dict) -> dict:
        self.validate_related_field(data["doc_type"], data)

        return data

    def validate_related_field(self, doc_type: str, data: dict) -> None:
        if not self.has_related_field(doc_type):
            return

        key = self.get_related_field_key(doc_type)
        if not data.get(key):
            raise serializers.ValidationError(f"参数 doc_type 为 {doc_type} 时，参数 {key} 不能为空")

    def has_related_field(self, doc_type: str) -> bool:
        return self.get_related_field_key(doc_type) in self.fields

    def get_related_field_key(self, doc_type: str) -> str:
        return f"related_{doc_type}"
