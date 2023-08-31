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

from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import SEMVER_PATTERN
from apigateway.core.models import Gateway, Resource, ResourceVersion
from apigateway.utils import time as time_utils


class ResourceVersionInfoSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    # TODO: 待开源版中，同步资源版本的服务全部切换为 version 后，此字段才能指定为必填: required=True
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=False)

    class Meta:
        model = ResourceVersion
        fields = [
            "gateway",
            "id",
            "version",
            "name",
            "title",
            "comment",
            "data",
            "created_by",
            "created_time",
        ]
        read_only_fields = ["id", "name", "data", "created_by", "created_time"]
        lookup_field = "id"

    def validate(self, data):
        self._validate_resource_count(data["gateway"])
        self._validate_version_unique(gateway=data["gateway"], version=data.get("version", ""))
        return data

    def _validate_version_unique(self, gateway: Gateway, version: str):
        # TODO: 临时跳过 version 校验，待提供 version 后，此部分删除
        if not version:
            return

        # ResourceVersion 中数据量较大，因此，不使用 UniqueTogetherValidator
        queryset = ResourceVersion.objects.filter(gateway=gateway, version=version)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(_("版本 {version} 已存在。").format(version=version))

    def _validate_resource_count(self, gateway):
        """
        校验网关下资源数量，网关下资源数量为0时，不允许创建网关版本
        """
        if not Resource.objects.filter(api_id=gateway.id).exists():
            raise serializers.ValidationError(_("请先创建资源，然后再生成版本。"))

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["data"] = instance.data_display

        # TODO: 用 name 数据初始化 version 数据后，此部分可删除
        result["version"] = instance.version or instance.name

        return result

    def create(self, validated_data):
        gateway = validated_data["gateway"]
        now = time_utils.now_datetime()

        # created_time：与版本名中时间保持一致，方便SDK使用此时间作为版本号
        name = ResourceVersionHandler().generate_version_name(gateway.name, now)
        validated_data.update(
            {
                "name": name,
                # TODO: 待 version 改为必填后，下面的 version 赋值去掉
                "version": validated_data.get("version") or name,
                "created_time": now,
            }
        )

        return super().create(validated_data)


class ResourceVersionListOutputSLZ(serializers.ModelSerializer):
    released_stages = serializers.SerializerMethodField()
    has_sdk = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()

    class Meta:
        model = ResourceVersion
        fields = (
            "id",
            "version",
            "name",
            "title",
            "comment",
            "resource_version_display",
            "created_time",
            "released_stages",
            "has_sdk",
        )
        read_only_fields = fields
        lookup_field = "id"

    def get_released_stages(self, obj):
        return self.context["released_stages"].get(obj["id"], [])

    def get_has_sdk(self, obj):
        return obj["id"] in self.context["resource_version_ids_has_sdk"]

    def get_version(self, obj):
        return obj.get("version") or obj.get("name", "")

    def get_resource_version_display(self, obj):
        return ResourceVersionHandler().get_resource_version_display(obj)


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
