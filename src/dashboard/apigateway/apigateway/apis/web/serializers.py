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

from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN

from .constants import BackendConfigSchemeEnum, BackendConfigTypeEnum, HashOnEnum, HashOnVarEnum, LoadBalanceTypeEnum


class HostSLZ(serializers.Serializer):
    scheme = serializers.ChoiceField(choices=BackendConfigSchemeEnum.get_choices(), help_text="协议")
    host = serializers.RegexField(HOST_WITHOUT_SCHEME_PATTERN, help_text="主机")
    weight = serializers.IntegerField(min_value=1, required=False, help_text="权重")

    class Meta:
        ref_name = "apis.web.HostSLZ"


class TimeoutSLZ(serializers.Serializer):
    connect = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1, help_text="连接超时时间")
    read = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1, help_text="读取超时时间")
    send = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1, help_text="写入超时时间")

    class Meta:
        ref_name = "apis.web.TimeoutSLZ"


class BaseBackendConfigSLZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=BackendConfigTypeEnum.get_choices(), default=BackendConfigTypeEnum.NODE.value, help_text="类型"
    )
    timeout = TimeoutSLZ(help_text="超时时间")
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices(), help_text="负载均衡")
    hosts = serializers.ListField(
        child=HostSLZ(),
        allow_empty=False,
        help_text="主机列表",
    )
    retries = serializers.IntegerField(required=False, default=0, help_text="重试次数", max_value=5)
    retry_timeout = serializers.IntegerField(required=False, default=0, help_text="重试超时时间")
    hash_on = serializers.CharField(
        required=False, default="", help_text="hash on", allow_blank=True, trim_whitespace=True
    )
    key = serializers.RegexField(
        r"^[a-zA-Z_][a-zA-Z0-9_-]*$",
        required=False,
        help_text="key",
        default="",
        allow_blank=True,
        max_length=255,
        trim_whitespace=True,
    )

    def validate_hosts(self, value):
        unique_combinations = set()
        for host_data in value:
            # 假设HostSLZ有scheme和host字段
            scheme_host_combination = (host_data["scheme"], host_data["host"])
            if scheme_host_combination in unique_combinations:
                raise serializers.ValidationError("hosts中的scheme和host组合必须唯一。")
            unique_combinations.add(scheme_host_combination)
        return value

    def validate(self, attrs):
        if attrs["loadbalance"] == LoadBalanceTypeEnum.CHASH.value:
            if attrs["hash_on"] not in dict(HashOnEnum.get_choices()):
                raise serializers.ValidationError("CHASH类型下必须指定hash_on")

            if attrs["key"] == "" or (
                attrs["hash_on"] == HashOnEnum.VARS.value and attrs["key"] not in dict(HashOnVarEnum.get_choices())
            ):
                raise serializers.ValidationError("CHASH类型下必须指定key")
        return attrs
