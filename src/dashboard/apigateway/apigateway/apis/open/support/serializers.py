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

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.core.models import Gateway


class APISDKQueryV1SLZ(serializers.Serializer):
    api_name = serializers.CharField(allow_null=True, default=None)
    api_id = serializers.IntegerField(allow_null=True, default=None)
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())

    def validate_api_id(self, value):
        if value:
            return value

        gateway_name = self.initial_data.get("gateway_name")
        if not gateway_name:
            return value

        gateway = Gateway.objects.filter(name=gateway_name).last()
        if not gateway:
            return value

        return gateway.pk


class SDKGenerateV1SLZ(serializers.Serializer):
    resource_version = serializers.CharField(max_length=128, help_text="资源版本")
    languages = serializers.ListField(
        child=serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices()),
        help_text="需要生成SDK的语言列表",
        default=[ProgrammingLanguageEnum.PYTHON.value],
    )
    version = serializers.CharField(default="", max_length=128, help_text="版本号")
