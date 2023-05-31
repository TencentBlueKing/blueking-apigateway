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
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import STAGE_ITEM_NAME_PATTERN, StageItemConfigStatusEnum, StageItemTypeEnum
from apigateway.core.models import StageItem


class StageItemSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    type = serializers.ChoiceField(choices=StageItemTypeEnum.get_choices())
    name = serializers.RegexField(regex=STAGE_ITEM_NAME_PATTERN)
    stage_item_configs = serializers.SerializerMethodField()

    class Meta:
        model = StageItem
        fields = (
            "id",
            "api",
            "type",
            "name",
            "description",
            "stage_item_configs",
        )
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=StageItem.objects.all(),
                fields=["api", "name"],
                message=gettext_lazy("网关下环境配置项名称已存在。"),
            ),
        ]

    def get_stage_item_configs(self, obj):
        return self.context["stage_item_configs"]

    def update(self, instance, validated_data):
        # 不允许更新类型
        validated_data["type"] = instance.type
        return super().update(instance, validated_data)


class ListStageItemSLZ(serializers.ModelSerializer):
    configured_stages = serializers.SerializerMethodField()
    not_configured_stages = serializers.SerializerMethodField()
    reference_instances = serializers.SerializerMethodField()

    class Meta:
        model = StageItem
        fields = (
            "id",
            "type",
            "name",
            "description",
            "updated_time",
            "configured_stages",
            "not_configured_stages",
            "reference_instances",
        )
        read_only_fields = fields
        lookup_field = "id"

    def get_configured_stages(self, obj):
        return self.context["stage_item_id_to_configured_stages"].get(obj.id, [])

    def get_not_configured_stages(self, obj):
        configured_stages = self.get_configured_stages(obj)
        configured_stage_ids = [stage["id"] for stage in configured_stages]

        return [
            stage
            for stage_id, stage in self.context["stage_id_to_fields"].items()
            if stage_id not in configured_stage_ids
        ]

    def get_reference_instances(self, obj):
        return self.context["stage_item_id_to_reference_instances"].get(obj.id, [])


class ListStageItemForStageSLZ(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = StageItem
        fields = (
            "id",
            "type",
            "name",
            "description",
            "updated_time",
            "status",
        )
        read_only_fields = fields
        lookup_field = "id"

    def get_status(self, obj):
        if obj.id in self.context["configured_item_ids"]:
            return StageItemConfigStatusEnum.CONFIGURED.value

        return StageItemConfigStatusEnum.NOT_CONFIGURED.value
