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
import json

from rest_framework import serializers
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.stage.serializers import StageSLZ
from apigateway.biz.stage import StageHandler
from apigateway.core.models import Stage


class StageV1SLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True)
    description_en = serializers.CharField(required=False, write_only=True)


class ResourceVersionInStageSLZ(serializers.Serializer):
    version = serializers.CharField()


class StageWithResourceVersionV1SLZ(serializers.Serializer):
    name = serializers.CharField()
    resource_version = ResourceVersionInStageSLZ(allow_null=True)
    released = serializers.SerializerMethodField()

    def to_representation(self, instance):
        instance.resource_version = self.context["stage_release"].get(instance.id, {}).get("resource_version")
        return super().to_representation(instance)

    def get_released(self, obj):
        return bool(obj.resource_version)


class StageSyncInputSLZ(StageSLZ):
    def update(self, instance, validated_data):
        # 未校验 resource version 中引用的 stage vars 是否存在，
        # 因此，不触发 update 信号，以防止误发布
        Stage.objects.filter(id=instance.id).update(
            description=validated_data.get("description"),
            description_en=validated_data.get("description_en"),
            _vars=json.dumps(vars),
            updated_by=validated_data.get("updated_by", ""),
        )

        StageHandler.save_related_data(
            instance,
            validated_data["proxy_http"],
            validated_data.get("rate_limit"),
        )

        StageHandler.add_update_audit_log(validated_data["api"], instance, validated_data.get("updated_by", ""))

        return instance
