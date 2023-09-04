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
from typing import List, Optional

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.biz.constants import SEMVER_PATTERN
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import ResourceVersion, Stage


class ReleaseV1SLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=False)
    resource_version_name = serializers.CharField(max_length=128, required=False)
    stage_names = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=True, default=list)
    comment = serializers.CharField(max_length=512, allow_blank=True, default="")

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["resource_version_id"] = self._get_resource_version_id(
            data["gateway"],
            data.get("version"),
            data.get("resource_version_name"),
        )
        data["stage_ids"] = self._get_stage_ids(data["gateway"], data["stage_names"])
        return data

    def _get_resource_version_id(self, gateway, version: Optional[str], resource_version_name: Optional[str]) -> int:
        if version:
            return self._get_resource_version_id_by_version(gateway, version)

        if resource_version_name:
            return self._get_resource_version_id_by_name(gateway, resource_version_name)

        raise serializers.ValidationError({"version": "请指定待发布的版本"})

    def _get_resource_version_id_by_name(self, gateway, resource_version_name: str) -> int:
        resource_version_id = ResourceVersion.objects.get_id_by_name(gateway, resource_version_name)
        if not resource_version_id:
            raise serializers.ValidationError(
                {
                    "resource_version_name": _("版本【{resource_version_name}】不存在。").format(
                        resource_version_name=resource_version_name,
                    ),
                }
            )

        return resource_version_id

    def _get_resource_version_id_by_version(self, gateway, version: str) -> int:
        resource_version_id = ResourceVersion.objects.get_id_by_version(gateway.id, version)
        if not resource_version_id:
            raise serializers.ValidationError({"version": _("版本【{version}】不存在。").format(version=version)})

        return resource_version_id

    def _get_stage_ids(self, gateway, stage_names: List[str]) -> List[int]:
        name_to_id_map = Stage.objects.get_name_id_map(gateway)

        # 如果未指定 stage_names，则默认处理网关下所有环境
        if not stage_names:
            return list(name_to_id_map.values())

        stage_ids = set()
        for stage_name in stage_names:
            if stage_name not in name_to_id_map:
                raise serializers.ValidationError(
                    {"stage_names": _("环境【{stage_name}】不存在。").format(stage_name=stage_name)}
                )
            stage_ids.add(name_to_id_map[stage_name])
        return list(stage_ids)


class QueryResourceVersionV1SLZ(serializers.Serializer):
    version = serializers.CharField(required=False)


class ListResourceVersionV1SLZ(serializers.Serializer):
    version = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True)
