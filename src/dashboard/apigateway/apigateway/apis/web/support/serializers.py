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
from apigateway.apps.support.models import APISDK
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.utils.time import now_datetime


class APISDKGenerateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    resource_version_id = serializers.IntegerField(required=True)
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices())
    include_private_resources = serializers.BooleanField(label="包含非公开资源")
    is_public = serializers.BooleanField(label="是否为公开", default=None)
    version = serializers.CharField(
        label="版本",
        default="",
        allow_null=True,
        allow_blank=True,
    )

    def validate(self, data):
        # 用户指定版本号的情况下，需要检查一下版本是否存在
        if data["version"]:
            if APISDK.objects.filter_sdk(
                gateway=data["gateway"],
                language=data["language"],
                version_number=data["version"],
            ).exists():
                raise serializers.ValidationError(_("版本已存在。"))

        latest_sdk = APISDK.objects.get_latest_sdk(gateway_id=data["gateway"].id, language=data["language"])
        if latest_sdk:
            self._validate_generate_too_soon(latest_sdk)
        return data

    def _validate_generate_too_soon(self, latest_sdk):
        if (now_datetime() - latest_sdk.created_time).total_seconds() <= 10:
            raise serializers.ValidationError(_("生成SDK操作过于频繁，请间隔 10 秒再试。"))

    def validate_is_public(self, value):
        # 兼容处理
        if value is None:
            return self.initial_data.get("need_upload_to_pypi", False)

        return value


class APISDKQueryInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices(), required=False)
    version_number = serializers.CharField(required=False, allow_blank=True)
    resource_version_id = serializers.IntegerField(allow_null=True, required=False)


class SDKListOutputSLZ(serializers.Serializer):
    download_url = serializers.CharField(source="instance.url")
    id = serializers.IntegerField(source="instance.id")
    resource_version_id = serializers.IntegerField(source="instance.resource_version.id")
    resource_version_name = serializers.CharField(source="instance.resource_version.name")
    resource_version_title = serializers.CharField(source="instance.resource_version.title")
    resource_version_display = serializers.CharField(source="instance.resource_version.object_display")
    language = serializers.CharField(source="language.value")
    version_number = serializers.CharField(source="instance.version_number")
    include_private_resources = serializers.BooleanField(source="instance.include_private_resources")
    is_public = serializers.BooleanField(source="instance.is_public")
    is_recommended = serializers.BooleanField(source="instance.is_recommended")
    created_time = serializers.DateTimeField(source="instance.created_time")
    updated_time = serializers.DateTimeField(source="instance.updated_time")
    config = serializers.DictField()
    name = serializers.CharField(source="instance.name")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(instance.config)
        return data

    class Meta:
        ref_name = "apps.support.api_sdk"
