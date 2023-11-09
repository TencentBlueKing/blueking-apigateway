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
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKListInputSLZ"


class SDKRetrieveInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )


class SDKDocInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKDocInputSLZ"


class SDKDocOutputSLZ(serializers.Serializer):
    content = serializers.CharField(help_text="文档内容")

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKDocOutputSLZ"


class SDKUsageExampleInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )
    system_name = serializers.CharField(help_text="组件所属系统名称")
    component_name = serializers.CharField(help_text="组件名称")


class SDKUsageExampleOutputSLZ(serializers.Serializer):
    content = serializers.CharField(help_text="文档内容")

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKUsageExampleOutputSLZ"


class SDKOutputSLZ(serializers.Serializer):
    board_label = serializers.CharField(help_text="组件 board 标签")
    sdk_name = serializers.CharField(help_text="SDK 名称")
    sdk_description = serializers.CharField(help_text="SDK 描述")
    sdk_version_number = serializers.CharField(help_text="SDK 版本号")
    sdk_download_url = serializers.CharField(help_text="SDK 下载链接")
    sdk_install_command = serializers.CharField(help_text="SDK 安装命令")

    class Meta:
        ref_name = "apigateway.apis.web.docs.esb.sdk.SDKOutputSLZ"
