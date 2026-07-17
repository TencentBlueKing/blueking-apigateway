# -*- coding: utf-8 -*-
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
from rest_framework import serializers

from apigateway.apps.support.constants import SDK_GENERATION_LANGUAGE_VALUES, ProgrammingLanguageEnum


class SDKGenerateV1SLZ(serializers.Serializer):
    resource_version = serializers.CharField(max_length=128, help_text="资源版本")
    languages = serializers.ListField(
        child=serializers.ChoiceField(choices=SDK_GENERATION_LANGUAGE_VALUES),
        help_text="需要生成SDK的语言列表",
        default=[ProgrammingLanguageEnum.PYTHON.value],
        allow_empty=False,
    )
