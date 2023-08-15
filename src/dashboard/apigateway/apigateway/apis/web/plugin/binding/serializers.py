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

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.common.fields import CurrentGatewayDefault


class PluginBindingSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    config_name = serializers.CharField(source="config.name", read_only=True)

    class Meta:
        model = PluginBinding
        fields = [
            "id",
            "api",
            "scope_type",
            "scope_id",
            "config_id",
            "config_name",
        ]


class PluginBindingBatchSLZ(serializers.Serializer):
    dry_run = serializers.BooleanField(default=False, write_only=True, help_text="试运行，仅返回可能影响的结果")
    scope_type = serializers.ChoiceField(
        write_only=True,
        choices=PluginBindingScopeEnum.get_choices(),
        help_text="绑定范围的类型",
    )
    scope_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        allow_empty=True,
        required=False,
        default=(),
        help_text="绑定范围的 IDs",
    )

    def validate_scope_ids(self, scope_ids):
        request = self.context["request"]
        request_scope_ids = set(scope_ids)
        valid_scope_ids = set(
            PluginBinding.objects.get_valid_scope_ids(
                request.gateway.pk,
                self.initial_data["scope_type"],
                request_scope_ids,
            )
        )

        if request_scope_ids != valid_scope_ids:
            raise serializers.ValidationError(f"contains invalid ids: {request_scope_ids - valid_scope_ids}")

        return scope_ids


class PluginBindingBatchResponseSLZ(serializers.Serializer):
    binds = serializers.ListField(child=PluginBindingSLZ(), read_only=True, help_text="生效的绑定")
    unbinds = serializers.ListField(child=PluginBindingSLZ(), read_only=True, help_text="解除的绑定")
    creates = serializers.ListField(child=PluginBindingSLZ(), read_only=True, help_text="新增的绑定")
    overwrites = serializers.ListField(child=PluginBindingSLZ(), read_only=True, help_text="覆盖的绑定")


class PluginBindingFilterSLZ(serializers.Serializer):
    scope_type = serializers.ListField(
        child=serializers.CharField(),
        source="scope_type__in",
        required=False,
        allow_empty=True,
        help_text="绑定范围的类型",
    )
    scope_id = serializers.ListField(
        child=serializers.IntegerField(),
        source="scope_id__in",
        required=False,
        allow_empty=True,
        help_text="绑定对象的 ID",
    )
