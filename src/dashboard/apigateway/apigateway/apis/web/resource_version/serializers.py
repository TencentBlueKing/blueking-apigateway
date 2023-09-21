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

from apigateway.biz.constants import SEMVER_PATTERN
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.validators import ResourceVersionValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import ResourceVersion


class ResourceVersionCreateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=True)
    comment = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data):
        validator = ResourceVersionValidator()
        validator(data)
        return data


class ResourceVersionRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    version = serializers.CharField()
    comment = serializers.CharField()
    data = serializers.SerializerMethodField()
    created_time = serializers.DateTimeField()
    created_by = serializers.CharField()

    def get_data(self, obj: ResourceVersion):
        return obj.data_display


class ResourceVersionListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    released_stages = serializers.SerializerMethodField()
    sdk_count = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    comment = serializers.CharField()
    created_time = serializers.DateTimeField()

    def get_released_stages(self, obj):
        return self.context["released_stages"].get(obj["id"], [])

    def get_sdk_count(self, obj):
        return self.context["resource_version_ids_sdk_count"].get(obj["id"], 0)

    def get_version(self, obj):
        return obj.get("version")

    def get_resource_version_display(self, obj):
        return ResourceVersionHandler.get_resource_version_display(obj)


class NeedNewVersionOutputSLZ(serializers.Serializer):
    need_new_version = serializers.BooleanField()


class ResourceVersionDiffQueryInputSLZ(serializers.Serializer):
    source_resource_version_id = serializers.IntegerField(allow_null=True)
    target_resource_version_id = serializers.IntegerField(allow_null=True)


class ResourceVersionResourceSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    method = serializers.CharField()
    path = serializers.CharField()
    diff = serializers.DictField(allow_null=True)


class ResourceVersionDiffOutputSLZ(serializers.Serializer):
    add = ResourceVersionResourceSLZ()
    delete = ResourceVersionResourceSLZ()
    update = serializers.DictField(child=ResourceVersionResourceSLZ())
