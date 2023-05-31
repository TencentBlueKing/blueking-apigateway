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

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding


class CurrentAccessStrategyDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context["access_strategy"]

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class AccessStrategyBindingBatchSLZ(serializers.Serializer):
    scope_type = serializers.ChoiceField(choices=AccessStrategyBindScopeEnum.choices())
    scope_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    type = serializers.ChoiceField(choices=AccessStrategyTypeEnum.get_choices())
    access_strategy = serializers.HiddenField(default=CurrentAccessStrategyDefault())

    def validate(self, data):
        if data["access_strategy"].type != data["type"]:
            raise serializers.ValidationError("策略绑定类型与策略类型不一致，请检查")
        return data


class AccessStrategyBindingBindSLZ(AccessStrategyBindingBatchSLZ):
    delete = serializers.BooleanField(default=False)


class AccessStrategyBindingQuerySLZ(serializers.Serializer):
    scope_type = serializers.ChoiceField(choices=AccessStrategyBindScopeEnum.choices())
    type = serializers.ChoiceField(choices=AccessStrategyTypeEnum.get_choices())


class AccessStrategyBindingListSLZ(serializers.ModelSerializer):
    class Meta:
        model = AccessStrategyBinding
        fields = [
            "scope_type",
            "scope_id",
            "type",
        ]


class AccessStrategyBindingDiffQuerySLZ(AccessStrategyBindingQuerySLZ):
    scope_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class AccessStrategyBindingDiffSLZ(serializers.ModelSerializer):
    access_strategy_id = serializers.SerializerMethodField()
    access_strategy_name = serializers.SerializerMethodField()

    class Meta:
        model = AccessStrategyBinding
        fields = [
            "scope_type",
            "scope_id",
            "type",
            "access_strategy_id",
            "access_strategy_name",
        ]

    def get_access_strategy_id(self, obj):
        if isinstance(obj, AccessStrategyBinding):
            return obj.access_strategy_id
        return 0

    def get_access_strategy_name(self, obj):
        if isinstance(obj, AccessStrategyBinding):
            return obj.access_strategy.name
        return ""


class AccessStrategyBindingDiffDataSLZ(serializers.Serializer):
    data = serializers.DictField(child=serializers.ListField(child=AccessStrategyBindingDiffSLZ()))
