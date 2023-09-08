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


class SDKListInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKListInputSLZ"


class SDKRetrieveInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())


class SDKDocInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKDocInputSLZ"


class SDKDocOutputSLZ(serializers.Serializer):
    content = serializers.CharField()

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKDocOutputSLZ"


class SDKUsageExampleInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())
    system_name = serializers.CharField()
    component_name = serializers.CharField()


class SDKUsageExampleOutputSLZ(serializers.Serializer):
    content = serializers.CharField()

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKUsageExampleOutputSLZ"


class SDKOutputSLZ(serializers.Serializer):
    board_label = serializers.CharField()
    sdk_name = serializers.CharField()
    sdk_description = serializers.CharField()
    sdk_version_number = serializers.CharField()
    sdk_download_url = serializers.CharField()
    sdk_install_command = serializers.CharField()

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKOutputSLZ"
