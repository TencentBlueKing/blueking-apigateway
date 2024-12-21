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

from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_type import GatewayTypeHandler
from apigateway.common.i18n.field import SerializerTranslatedField


class GatewayQueryInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="网关筛选条件，支持模糊匹配网关名称、描述"
    )


class GatewayOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="网关 ID")
    name = serializers.CharField(help_text="网关名称")
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, help_text="网关描述")
    tenant_mode = serializers.CharField(read_only=True, help_text="租户模式")
    tenant_id = serializers.CharField(read_only=True, help_text="租户 ID")
    maintainers = serializers.ListField(help_text="网关负责人")
    is_official = serializers.SerializerMethodField(help_text="是否为官方网关, true: 是, false: 否")
    api_url = serializers.SerializerMethodField(help_text="网关访问地址")
    sdks = serializers.SerializerMethodField(help_text="SDK")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.gateway.serializers.GatewayOutputSLZ"

    def get_api_url(self, obj):
        return GatewayHandler.get_api_domain(obj)

    def get_is_official(self, obj):
        return GatewayTypeHandler.is_official(self.context["gateway_auth_configs"][obj.id].gateway_type)

    def get_sdks(self, obj):
        return self.context["gateway_sdks"].get(obj.id, [])
