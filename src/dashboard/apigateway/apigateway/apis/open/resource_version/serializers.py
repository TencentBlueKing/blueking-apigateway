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
from typing import Optional

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.biz.constants import SEMVER_PATTERN
from apigateway.biz.stage import StageHandler
from apigateway.biz.validators import ResourceVersionValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import ResourceVersion


class ReleaseV1InputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=False)
    # remove the name from ResourceVersion
    # resource_version_name = serializers.CharField(max_length=128, allow_blank=True, required=False)
    stage_names = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=True, default=list)
    comment = serializers.CharField(max_length=512, allow_blank=True, default="")

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["resource_version_id"] = self._get_resource_version_id(
            data["gateway"],
            data.get("version"),
        )
        data["stage_ids"] = StageHandler.get_stage_ids(data["gateway"], data["stage_names"])
        return data

    def _get_resource_version_id(self, gateway, version: Optional[str]) -> int:
        if version:
            resource_version_id = ResourceVersion.objects.get_id_by_version(gateway.id, version)
            if not resource_version_id:
                raise serializers.ValidationError({"version": _("版本【{version}】不存在。").format(version=version)})
            return resource_version_id

        raise serializers.ValidationError({"version": "请指定待发布的版本"})


class ResourceVersionCreateV1InputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=True)
    comment = serializers.CharField(allow_blank=True, allow_null=True, max_length=512, required=False)

    class Meta:
        validators = [ResourceVersionValidator()]


class ResourceVersionQueryV1InputSLZ(serializers.Serializer):
    version = serializers.CharField(required=False)


class ResourceVersionListV1OutputSLZ(serializers.Serializer):
    version = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True)
