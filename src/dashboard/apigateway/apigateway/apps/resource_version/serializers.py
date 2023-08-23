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
import datetime

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.funcs import get_resource_version_display
from apigateway.core.constants import SEMVER_PATTERN
from apigateway.core.models import Gateway, Resource, ResourceVersion
from apigateway.utils import time as time_utils
from apigateway.utils.string import random_string


class ResourceVersionSLZ(serializers.ModelSerializer):
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

    def _validate_resource_count(self, api):
        """
        校验网关下资源数量，网关下资源数量为0时，不允许创建网关版本
        """
        if not Resource.objects.filter(api_id=api.id).exists():
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
        name = self._generate_version_name(gateway.name, now)
        validated_data.update(
            {
                "name": name,
                # TODO: 待 version 改为必填后，下面的 version 赋值去掉
                "version": validated_data.get("version") or name,
                "created_time": now,
            }
        )

        return super().create(validated_data)

    def _generate_version_name(self, gateway_name: str, now: datetime.datetime) -> str:
        """生成新的版本名称"""
        return "{gateway_name}_{now_str}_{random_str}".format(
            gateway_name=gateway_name,
            now_str=time_utils.format(now, fmt="YYYYMMDDHHmmss"),
            random_str=random_string(5),
        )


class ResourceVersionUpdateSLZ(serializers.ModelSerializer):
    title = serializers.CharField(label="版本名称", max_length=128, required=True)
    comment = serializers.CharField(label="版本说明", max_length=512, allow_blank=True, required=False)

    class Meta:
        model = ResourceVersion
        fields = [
            "title",
            "comment",
        ]
        lookup_field = "id"


class ResourceVersionListSLZ(serializers.ModelSerializer):
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
        return get_resource_version_display(obj)


class NeedNewVersionSLZ(serializers.Serializer):
    need_new_version = serializers.BooleanField()


class ResourceVersionDiffQuerySLZ(serializers.Serializer):
    source_resource_version_id = serializers.IntegerField(allow_null=True)
    target_resource_version_id = serializers.IntegerField(allow_null=True)


class ResourceVersionResourceSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    method = serializers.CharField()
    path = serializers.CharField()
    diff = serializers.DictField(allow_null=True)


class ResourceVersionDiffSLZ(serializers.Serializer):
    add = ResourceVersionResourceSLZ()
    delete = ResourceVersionResourceSLZ()
    update = serializers.DictField(child=ResourceVersionResourceSLZ())
