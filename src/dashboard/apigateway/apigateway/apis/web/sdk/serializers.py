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
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.apps.support.models import GatewaySDK
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.utils.time import now_datetime


class GatewaySDKGenerateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    resource_version_id = serializers.IntegerField(required=True)
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())
    version = serializers.CharField(
        label="版本",
        default="",
        allow_null=True,
        allow_blank=True,
    )

    def validate(self, data):
        # 用户指定版本号的情况下，需要检查一下版本是否存在
        if (
            data["version"]
            and GatewaySDK.objects.filter(
                gateway=data["gateway"],
                language=data["language"],
                version_number=data["version"],
            ).exists()
        ):
            raise serializers.ValidationError(_("版本已存在。"))

        latest_sdk = GatewaySDK.objects.get_latest_sdk(gateway_id=data["gateway"].id, language=data["language"])
        if latest_sdk:
            self._validate_generate_too_soon(latest_sdk)
        return data

    def _validate_generate_too_soon(self, latest_sdk):
        if (now_datetime() - latest_sdk.created_time).total_seconds() <= 10:
            raise serializers.ValidationError(_("生成SDK操作过于频繁，请间隔 10 秒再试。"))


class GatewaySDKQueryInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices(), required=False)
    version_number = serializers.CharField(required=False, allow_blank=True)
    resource_version_id = serializers.IntegerField(allow_null=True, required=False)


class ResourceVersionInfoSlz(serializers.Serializer):
    id = serializers.IntegerField()
    version = serializers.CharField()
    resource_version_display = serializers.CharField(source="object_display")


class GatewaySDKListOutputSLZ(serializers.Serializer):
    download_url = serializers.CharField(source="instance.url")
    id = serializers.IntegerField(source="instance.id")
    language = serializers.CharField(source="language.value")
    version_number = serializers.CharField(source="instance.version_number")
    created_time = serializers.DateTimeField(source="instance.created_time")
    updated_time = serializers.DateTimeField(source="instance.updated_time")
    created_by = serializers.CharField(source="instance.created_by")
    name = serializers.CharField(source="instance.name")
    resource_version = ResourceVersionInfoSlz(source="instance.resource_version")

    class Meta:
        ref_name = "apigateway.apps.support.models"
