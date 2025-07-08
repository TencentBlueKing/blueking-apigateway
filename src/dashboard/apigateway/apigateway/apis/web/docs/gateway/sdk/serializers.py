# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.common.i18n.field import SerializerTranslatedField


class GatewaySLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="网关 ID")
    name = serializers.CharField(read_only=True, help_text="网关名称")
    description = SerializerTranslatedField(
        translated_fields={"en": "description_en"}, read_only=True, help_text="网关描述"
    )

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.sdk.serializers.GatewaySLZ"


class SDKDocInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.sdk.serializers.SDKDocInputSLZ"


class SDKDocOutputSLZ(serializers.Serializer):
    content = serializers.CharField(allow_blank=True, help_text="文档内容")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.sdk.serializers.SDKDocOutputSLZ"
