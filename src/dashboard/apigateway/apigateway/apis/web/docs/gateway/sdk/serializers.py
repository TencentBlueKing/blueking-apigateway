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
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.support.api_sdk.models import SDKFactory
from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.resource_version import ResourceVersionHandler


class SdkListInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())


class GatewaySLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(translated_fields={"en": "description_en"}, read_only=True)


class SdkListOutputSLZ(serializers.Serializer):
    gateway = GatewaySLZ()
    sdk = serializers.SerializerMethodField()
    resource_version = serializers.SerializerMethodField()
    # 资源版本已发布的环境
    released_stages = serializers.SerializerMethodField()

    def get_sdk(self, obj):
        return SDKFactory.create(obj).as_dict()

    def get_resource_version(self, obj):
        resource_version = self.context[obj.resource_version_id]
        return {
            "id": resource_version["id"],
            "display": ResourceVersionHandler.get_resource_version_display(resource_version),
        }

    def get_released_stages(self, obj):
        return self.context["released_stages"].get(obj.resource_version_id, [])


class SdkDocInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())
