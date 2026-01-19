# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from apigateway.biz.validators import UpstreamValidator
from apigateway.common.security import is_forbidden_host
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN, HashOnTypeEnum, LoadBalanceTypeEnum

from .constants import BackendConfigSchemeEnum, BackendConfigTypeEnum


class HostSLZ(serializers.Serializer):
    scheme = serializers.ChoiceField(choices=BackendConfigSchemeEnum.get_choices(), help_text="协议")
    host = serializers.RegexField(HOST_WITHOUT_SCHEME_PATTERN, help_text="主机")
    weight = serializers.IntegerField(min_value=1, required=False, help_text="权重")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.HostSLZ"


# Health Check Serializers
class BaseHealthySLZ(serializers.Serializer):
    """Base serializer for healthy configurations"""

    http_statuses = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_null=True,
        help_text="HTTP状态码列表",
    )
    successes = serializers.IntegerField(
        min_value=1, max_value=254, required=False, allow_null=True, help_text="成功次数"
    )


class PassiveHealthySLZ(BaseHealthySLZ):
    """Passive health check healthy configuration"""

    class Meta:
        ref_name = "apigateway.apis.web.serializers.PassiveHealthySLZ"


class ActiveHealthySLZ(BaseHealthySLZ):
    """Active health check healthy configuration"""

    interval = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="检查间隔(秒)")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.ActiveHealthySLZ"


class BaseUnhealthySLZ(serializers.Serializer):
    """Base serializer for unhealthy configurations"""

    http_statuses = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_null=True,
        help_text="HTTP状态码列表",
    )
    http_failures = serializers.IntegerField(
        min_value=1, max_value=254, required=False, allow_null=True, help_text="HTTP失败次数"
    )
    tcp_failures = serializers.IntegerField(
        min_value=1, max_value=254, required=False, allow_null=True, help_text="TCP失败次数"
    )
    timeouts = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="超时次数")


class PassiveUnhealthySLZ(BaseUnhealthySLZ):
    """Passive health check unhealthy configuration"""

    class Meta:
        ref_name = "apigateway.apis.web.serializers.PassiveUnhealthySLZ"


class ActiveUnhealthySLZ(BaseUnhealthySLZ):
    """Active health check unhealthy configuration"""

    interval = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="检查间隔(秒)")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.ActiveUnhealthySLZ"


class ActiveCheckSLZ(serializers.Serializer):
    """Active health check configuration"""

    type = serializers.ChoiceField(
        choices=[("http", "HTTP"), ("https", "HTTPS"), ("tcp", "TCP")], default="http", help_text="检查类型"
    )
    timeout = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="超时时间(秒)")
    concurrency = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="并发数")
    http_path = serializers.CharField(required=False, allow_null=True, help_text="HTTP检查路径")
    https_verify_certificate = serializers.BooleanField(required=False, allow_null=True, help_text="HTTPS证书验证")
    # NOTE: 暂时不支持，后续再支持
    # host = serializers.CharField(required=False, allow_null=True, help_text="主机名")
    # port = serializers.IntegerField(min_value=1, max_value=65535, required=False, allow_null=True, help_text="端口")
    # req_headers = serializers.ListField(
    #     child=serializers.CharField(), required=False, allow_null=True, help_text="请求头"
    # )
    healthy = ActiveHealthySLZ(required=False, allow_null=True, help_text="健康配置")
    unhealthy = ActiveUnhealthySLZ(required=False, allow_null=True, help_text="不健康配置")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.ActiveCheckSLZ"


class PassiveCheckSLZ(serializers.Serializer):
    """Passive health check configuration"""

    type = serializers.ChoiceField(
        choices=[("http", "HTTP"), ("https", "HTTPS"), ("tcp", "TCP")], default="http", help_text="检查类型"
    )
    healthy = PassiveHealthySLZ(required=False, allow_null=True, help_text="健康配置")
    unhealthy = PassiveUnhealthySLZ(required=False, allow_null=True, help_text="不健康配置")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.PassiveCheckSLZ"


class CheckSLZ(serializers.Serializer):
    """Health check configuration (active and/or passive)"""

    active = ActiveCheckSLZ(required=False, allow_null=True, help_text="主动健康检查")
    passive = PassiveCheckSLZ(required=False, allow_null=True, help_text="被动健康检查")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.CheckSLZ"

    def validate(self, attrs):
        """Ensure at least one of active or passive is provided"""
        active = attrs.get("active")
        passive = attrs.get("passive")

        if not active and not passive:
            raise serializers.ValidationError("至少需要配置主动健康检查或被动健康检查中的一项")

        return attrs


class BaseBackendConfigSLZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=BackendConfigTypeEnum.get_choices(), default=BackendConfigTypeEnum.NODE.value, help_text="类型"
    )
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1, help_text="超时时间")
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices(), help_text="负载均衡")
    # if loadbalance is chash, hash_on is required
    hash_on = serializers.ChoiceField(choices=HashOnTypeEnum.get_choices(), help_text="hash 类型", required=False)
    # if hash_on is not empty, key is required
    key = serializers.CharField(help_text="hash 键", required=False)
    hosts = serializers.ListField(
        child=HostSLZ(),
        allow_empty=False,
        help_text="主机列表",
    )
    checks = CheckSLZ(required=False, allow_null=True, help_text="健康检查配置")

    class Meta:
        ref_name = "apigateway.apis.web.serializers.BaseBackendConfigSLZ"
        validators = [UpstreamValidator()]

    def validate_hosts(self, value):
        unique_combinations = set()
        for host_data in value:
            # 假设 HostSLZ 有 scheme 和 host 字段
            scheme_host_combination = (host_data["scheme"], host_data["host"])
            if scheme_host_combination in unique_combinations:
                raise serializers.ValidationError("hosts 中的 scheme 和 host 组合必须唯一。")
            unique_combinations.add(scheme_host_combination)

            if is_forbidden_host(host_data["host"]):
                raise serializers.ValidationError(f"host: {host_data['host']} 不能使用该端口。")

        return value
