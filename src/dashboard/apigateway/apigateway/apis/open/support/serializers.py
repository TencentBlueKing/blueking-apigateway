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
from apigateway.biz.resource_version import ResourceVersionHandler
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
    include_private_resources = serializers.BooleanField(default=False, help_text="是否包含私有资源")
    version = serializers.CharField(default="", max_length=128, help_text="版本号")


class APISDKV1SLZ(serializers.Serializer):
    api_id = serializers.IntegerField(source="instance.gateway_id")
    api_name = serializers.SerializerMethodField()
    api_description = serializers.SerializerMethodField()
    user_auth_type = serializers.SerializerMethodField()
    language = serializers.CharField(read_only=True, source="language.value")

    # TODO: version_number/download_url，在API帮助中心升级后，可删除
    version_number = serializers.CharField(read_only=True, source="instance.version_number")
    download_url = serializers.CharField(read_only=True, source="instance.url")

    sdk_version_number = serializers.CharField(read_only=True, source="instance.version_number")
    sdk_download_url = serializers.CharField(read_only=True, source="instance.url")
    sdk_name = serializers.CharField(read_only=True, source="instance.name")
    sdk_install_command = serializers.CharField(read_only=True, source="install_command")
    sdk_created_time = serializers.DateTimeField(read_only=True, source="instance.created_time")

    resource_version_name = serializers.SerializerMethodField()
    resource_version_title = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()
    released_stages = serializers.SerializerMethodField()

    def get_api_name(self, obj):
        return self.context["gateway_id_map"][obj.instance.gateway_id].name

    def get_api_description(self, obj):
        return self.context["gateway_id_map"][obj.instance.gateway_id].description

    def get_user_auth_type(self, obj):
        return self.context["gateway_id_config_map"][obj.instance.gateway_id]["user_auth_type"]

    def get_resource_version_name(self, obj):
        return self.context["resource_versions"][obj.instance.resource_version_id]["name"]

    def get_resource_version_title(self, obj):
        return self.context["resource_versions"][obj.instance.resource_version_id]["title"]

    def get_resource_version_display(self, obj):
        resource_version_data = self.context["resource_versions"][obj.instance.resource_version_id]
        return ResourceVersionHandler.get_resource_version_display(resource_version_data)

    def get_released_stages(self, obj):
        return self.context["released_stages"].get(obj.instance.resource_version_id, [])
