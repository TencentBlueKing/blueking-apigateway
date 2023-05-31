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

from apigateway.apps.access_strategy.binding.serializers import CurrentAccessStrategyDefault
from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding, IPGroup
from apigateway.common.constants import IP_OR_SEGMENT_PATTERN
from apigateway.core.scopes import ScopeManager
from apigateway.core.signals import reversion_update_signal

from .constants import IPGroupActionEnum


class IPGroupV1SLZ(serializers.Serializer):
    name = serializers.CharField(max_length=64)
    ips = serializers.CharField(allow_blank=True)
    comment = serializers.CharField(allow_blank=True, max_length=512, required=False)
    action = serializers.ChoiceField(choices=IPGroupActionEnum.choices())

    def validate_ips(self, value):
        return self._get_valid_ips(value)

    def _get_valid_ips(self, value):
        if not value:
            return ""

        # split with \n\r, then ignore blank line and `# comment`
        valid_ips = []
        for line in value.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if not IP_OR_SEGMENT_PATTERN.match(line):
                raise serializers.ValidationError(_("包含非IP数据【{line}】。").format(line=line))

            valid_ips.append(line)

        return "\n".join(valid_ips)


class AccessStrategyAddIPGroupsV1SLZ(serializers.Serializer):
    access_strategy_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    ip_group_list = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)

    def validate_access_strategy_ids(self, value):
        ids = set(
            AccessStrategy.objects.filter(
                api=self.context["request"].gateway, type=AccessStrategyTypeEnum.IP_ACCESS_CONTROL.value, id__in=value
            ).values_list("id", flat=True)
        )
        if set(value) != ids:
            raise serializers.ValidationError(_("包含非网关下的IP访问控制策略。"))

        return list(ids)

    def validate_ip_group_list(self, value):
        ids = set(
            IPGroup.objects.filter(api=self.context["request"].gateway, id__in=value).values_list("id", flat=True)
        )
        if set(value) != ids:
            raise serializers.ValidationError(_("包含非网关下的IP分组。"))

        return list(ids)


class AccessStrategyScopeSLZ(serializers.Serializer):
    name = serializers.CharField()


class AccessStrategyBindingSyncSLZ(serializers.Serializer):
    access_strategy = serializers.HiddenField(default=CurrentAccessStrategyDefault())
    scope_type = serializers.ChoiceField(choices=AccessStrategyBindScopeEnum.choices())
    scopes = serializers.ListField(child=AccessStrategyScopeSLZ(), allow_empty=True, required=False)
    type = serializers.ChoiceField(choices=AccessStrategyTypeEnum.get_choices())

    def validate(self, data):
        if data["access_strategy"].type != data["type"]:
            raise serializers.ValidationError(_("策略绑定类型与策略类型不一致，请检查。"))
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        data["valid_scope_ids"] = self._get_valid_scope_ids(data["scope_type"], data.get("scopes"))

        return data

    def _get_valid_scope_ids(self, scope_type: str, scopes: Optional[list]) -> List[int]:
        valid_scope_ids = ScopeManager.get_manager(scope_type).get_scope_ids(
            self.context["request"].gateway.id,
            scopes,
        )
        if scopes and len(valid_scope_ids) != len(scopes):
            raise serializers.ValidationError(
                {
                    "scopes": _("指定的部分对象不存在。"),
                }
            )
        return valid_scope_ids

    def save(self, **kwargs):
        validated_data = dict(list(self.validated_data.items()) + list(kwargs.items()))
        request = self.context["request"]
        for scope_id in validated_data["valid_scope_ids"]:
            binding, created = AccessStrategyBinding.objects.get_or_create(
                scope_type=validated_data["scope_type"],
                scope_id=scope_id,
                type=validated_data["type"],
                defaults={
                    "access_strategy": validated_data["access_strategy"],
                    "created_by": request.user.username,
                    "updated_by": request.user.username,
                },
            )
            if not created:
                binding.access_strategy = validated_data["access_strategy"]
                binding.updated_by = request.user.username
                binding.save()

        # 同步策略绑定时，本次未指定的对象，解除绑定
        AccessStrategyBinding.objects.filter(
            access_strategy=validated_data["access_strategy"],
            scope_type=validated_data["scope_type"],
            type=validated_data["type"],
        ).exclude(scope_id__in=validated_data["valid_scope_ids"]).delete()

        # 发送信号，告知对象绑定的策略发生了变动
        reversion_update_signal.send(sender=AccessStrategyBinding, instance_id=None, action="bind")
