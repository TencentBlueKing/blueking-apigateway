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
from apigateway.biz.validators import ResourceVersionValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import ResourceVersion


class ResourceVersionCreateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=True, help_text="版本号")
    comment = serializers.CharField(allow_blank=True, required=False, help_text="版本日志")

    class Meta:
        validators = [ResourceVersionValidator()]


class ResourceVersionRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    version = serializers.CharField(help_text="版本号")
    comment = serializers.CharField(help_text="版本日志")
    data = serializers.SerializerMethodField(help_text="版本数据")
    created_time = serializers.DateTimeField(help_text="创建时间")
    created_by = serializers.CharField(help_text="创建人")

    def get_data(self, obj: ResourceVersion):
        return obj.data_display


class ResourceVersionListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    released_stages = serializers.SerializerMethodField(help_text="已发布的环境列表")
    sdk_count = serializers.SerializerMethodField(help_text="生成skd数量")
    version = serializers.SerializerMethodField(help_text="版本号")
    comment = serializers.CharField(help_text="版本日志")
    created_time = serializers.DateTimeField(help_text="创建时间")

    def get_released_stages(self, obj):
        return self.context["released_stages"].get(obj["id"], [])

    def get_sdk_count(self, obj):
        return self.context["resource_version_ids_sdk_count"].get(obj["id"], 0)

    def get_version(self, obj):
        return obj.get("version")


class NeedNewVersionOutputSLZ(serializers.Serializer):
    need_new_version = serializers.BooleanField(help_text="是否需要生成版本")


class ResourceVersionDiffQueryInputSLZ(serializers.Serializer):
    source_resource_version_id = serializers.IntegerField(allow_null=True, help_text="对比源的版本号id")
    target_resource_version_id = serializers.IntegerField(allow_null=True, help_text="对比目标的版本号id")


class ResourceVersionResourceSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    name = serializers.CharField(help_text="资源名称")
    method = serializers.CharField(help_text="请求方法")
    path = serializers.CharField(help_text="请求路径")
    diff = serializers.DictField(help_text="对比差异", allow_null=True)


class ResourceVersionDiffOutputSLZ(serializers.Serializer):
    add = ResourceVersionResourceSLZ()
    delete = ResourceVersionResourceSLZ()
    update = serializers.DictField(child=ResourceVersionResourceSLZ())
