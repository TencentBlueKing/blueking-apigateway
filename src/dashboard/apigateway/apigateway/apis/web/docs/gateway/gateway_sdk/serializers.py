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
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.gateway_sdk.SDKListInputSLZ"


class StageSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="网关环境 ID")
    name = serializers.CharField(read_only=True, help_text="网关环境名称")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.gateway_sdk.StageSLZ"


class ResourceVersionSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源版本 ID")
    version = serializers.CharField(read_only=True, help_text="资源版本号")


class SDKSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True, help_text="SDK 名称")
    version = serializers.CharField(read_only=True, help_text="SDK 版本号")
    url = serializers.CharField(read_only=True, help_text="SDK 下载链接")
    install_command = serializers.CharField(read_only=True, help_text="SDK 安装命令")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.gateway_sdk.SDKSLZ"


class StageSDKOutputSLZ(serializers.Serializer):
    stage = StageSLZ(help_text="网关环境")
    resource_version = ResourceVersionSLZ(help_text="资源版本")
    sdk = SDKSLZ(allow_null=True, help_text="SDK")


class SDKUsageExampleInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )
    stage_name = serializers.CharField(help_text="网关环境名称")
    resource_name = serializers.CharField(help_text="资源名称")
    # todo：暂时先不加
    resource_id = serializers.IntegerField(help_text="资源id", required=False)


class SDKUsageExampleOutputSLZ(serializers.Serializer):
    content = serializers.CharField(allow_blank=True, help_text="文档内容")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.gateway_sdk.SDKUsageExampleOutputSLZ"
