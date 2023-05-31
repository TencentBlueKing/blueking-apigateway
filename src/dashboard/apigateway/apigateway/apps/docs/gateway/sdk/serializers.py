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

from apigateway.apps.docs.gateway.constants_ext import UserAuthTypeEnum
from apigateway.common.constants import ChoiceEnum


class ProgrammingLanguageEnum(ChoiceEnum):
    PYTHON = "python"


class SDKQuerySLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.choices())


class SDKDocConditionSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.choices())


class SDKUsageExampleConditionSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.choices())


class SDKSLZ(serializers.Serializer):
    language = serializers.CharField(read_only=True)
    sdk_name = serializers.CharField(read_only=True)
    sdk_version_number = serializers.CharField(read_only=True)
    sdk_download_url = serializers.CharField(read_only=True)
    sdk_install_command = serializers.CharField(read_only=True)


class GatewaySDKSLZ(SDKSLZ):
    api_id = serializers.IntegerField()
    api_name = serializers.CharField(read_only=True)
    api_description = serializers.CharField(read_only=True)
    user_auth_type = serializers.CharField(read_only=True)
    user_auth_type_display = serializers.SerializerMethodField()
    resource_version_name = serializers.CharField()
    resource_version_title = serializers.CharField()
    resource_version_display = serializers.CharField()
    released_stages = serializers.ListField()

    def get_user_auth_type_display(self, obj):
        return UserAuthTypeEnum.get_choice_label(obj["user_auth_type"])


class StageSDKSLZ(SDKSLZ):
    stage_name = serializers.CharField()
    resource_version_name = serializers.CharField()
    resource_version_title = serializers.CharField()
    resource_version_display = serializers.CharField()
