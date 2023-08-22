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
import itertools
import operator

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.access_strategy.constants import (
    ALLOWED_ORIGIN_PATTERN,
    AccessStrategyTypeEnum,
    CircuitBreakerBackOffTypeEnum,
    CircuitBreakerStrategyTypeEnum,
    IPAccessControlTypeEnum,
)
from apigateway.apps.access_strategy.models import AccessStrategy
from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.stage.serializers import RateSLZ
from apigateway.biz.validators import BKAppCodeListValidator
from apigateway.common.factories import SchemaFactory
from apigateway.common.fields import CurrentGatewayDefault, DurationInSecondField
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.core.constants import HTTP_METHOD_CHOICES
from apigateway.core.signals import reversion_update_signal


class AccessStrategyQuerySLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=AccessStrategyTypeEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "type", "-type", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class IPAccessControlSLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=IPAccessControlTypeEnum.choices())
    ip_group_list = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class AccessStrategyRateSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(allow_blank=True, default="")
    tokens = serializers.IntegerField(min_value=0)
    period = serializers.IntegerField(min_value=1)


class AccessStrategyRateLimitSLZ(serializers.Serializer):
    """
    rates 为初始版本，但是 openapi 中为了更方便用户配置、更好的扩展性，改用 rates_config
    - rates_config 中，如果包含多项 bk_app_code 的配置，即可扩展为支持单个应用配置多个频率
    """

    rates = serializers.DictField(child=RateSLZ(many=True), allow_empty=True, required=False)
    rates_config = serializers.ListField(child=AccessStrategyRateSLZ(), allow_empty=True, required=False)

    def validate(self, data):
        if data.get("rates"):
            return {"rates": data["rates"]}

        if data.get("rates_config"):
            return {"rates": data["rates_config"]}

        return {}

    def validate_rates_config(self, value: list) -> dict:
        rates = {}

        sorted_value = sorted(value, key=operator.itemgetter("bk_app_code"))
        for bk_app_code, group in itertools.groupby(sorted_value, key=operator.itemgetter("bk_app_code")):
            # 默认频率限制，应用指定为：__default
            bk_app_code = bk_app_code or "__default"
            rates[bk_app_code] = [
                {
                    "tokens": config["tokens"],
                    "period": config["period"],
                }
                for config in group
            ]
            # 当前每个应用，只能指定一条频率配置
            if len(rates[bk_app_code]) != 1:
                raise serializers.ValidationError(f"应用[{bk_app_code}]的频率配置超过一条")

        return rates


class UserVerifiedUnrequiredAppsSLZ(serializers.Serializer):
    bk_app_code_list = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        validators=[BKAppCodeListValidator()],
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["bk_app_code_list"] = sorted(data["bk_app_code_list"])
        return data


class AccessStrategyCORSSLZ(serializers.Serializer):
    allowed_origins = serializers.ListField(child=serializers.RegexField(ALLOWED_ORIGIN_PATTERN), allow_empty=False)
    allowed_methods = serializers.ListField(
        child=serializers.ChoiceField(choices=HTTP_METHOD_CHOICES), allow_empty=False
    )
    allowed_headers = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    exposed_headers = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    max_age = serializers.IntegerField(min_value=0, required=False)
    allow_credentials = serializers.BooleanField(required=False)
    option_passthrough = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        # max_age 非法时，去除该值
        if "max_age" in data and not str(data["max_age"]).isdigit():
            data.pop("max_age")

        return super().to_internal_value(data)

    def validate(self, data):
        # 网关代理 cors 响应，预检的 options 请求不向后传递
        data["option_passthrough"] = False

        return data


class CBWindowSLZ(serializers.Serializer):
    duration = DurationInSecondField(required=True, min_value=1)
    buckets = serializers.HiddenField(default=10)


class CBConditionsSLZ(serializers.Serializer):
    http_error = serializers.BooleanField(required=False, default=False)
    status_code = serializers.ListField(
        child=serializers.IntegerField(min_value=200, max_value=999),
        allow_empty=True,
        required=False,
        default=list,
    )
    timeout = serializers.BooleanField(required=False, default=False)
    network_error = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        if data["http_error"] and not data["status_code"]:
            raise serializers.ValidationError("断路器触发条件包含后端响应状态码错误时，错误状态码不能为空")

        if not data["http_error"] and data["status_code"]:
            raise serializers.ValidationError("断路器触发条件不包含后端响应状态码错误时，错误状态码需为空")

        return data


class CBStrategyOptionsSLZ(serializers.Serializer):
    threshold = serializers.IntegerField(required=True, min_value=1)
    rate = serializers.HiddenField(default=0)
    min_samples = serializers.HiddenField(default=0)


class CBStrategySLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=CircuitBreakerStrategyTypeEnum.choices())
    options = CBStrategyOptionsSLZ()


class CBBackOffOptionsSLZ(serializers.Serializer):
    interval = DurationInSecondField(required=True, min_value=1)


class CBBackOffSLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=CircuitBreakerBackOffTypeEnum.choices())
    options = CBBackOffOptionsSLZ()


class CircuitBreakerSLZ(serializers.Serializer):
    window = CBWindowSLZ()
    conditions = CBConditionsSLZ()
    strategy = CBStrategySLZ()
    back_off = CBBackOffSLZ()


class AccessStrategySLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    ip_access_control = IPAccessControlSLZ(allow_null=True, required=False)
    rate_limit = AccessStrategyRateLimitSLZ(allow_null=True, required=False)
    user_verified_unrequired_apps = UserVerifiedUnrequiredAppsSLZ(allow_null=True, required=False)
    error_status_code_200 = serializers.DictField(allow_null=True, required=False)
    cors = AccessStrategyCORSSLZ(allow_null=True, required=False)
    circuit_breaker = CircuitBreakerSLZ(allow_null=True, required=False)

    class Meta:
        model = AccessStrategy
        fields = (
            "id",
            "api",
            "name",
            "type",
            "comment",
            "ip_access_control",
            "rate_limit",
            "user_verified_unrequired_apps",
            "error_status_code_200",
            "cors",
            "circuit_breaker",
        )
        read_only_fields = ("id",)
        non_model_fields = [
            "ip_access_control",
            "rate_limit",
            "user_verified_unrequired_apps",
            "error_status_code_200",
            "cors",
            "circuit_breaker",
        ]
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=AccessStrategy.objects.all(),
                fields=("api", "name", "type"),
                message="网关下策略名称+类型已经存在，请检查",
            )
        ]

    def validate(self, data):
        access_strategy_type = data["type"]
        data["config"] = data.get(access_strategy_type)
        if not data["config"]:
            raise serializers.ValidationError("策略配置不允许为空")

        return data

    def validate_ip_access_control(self, value):
        if self.instance and value and self.instance.config.get("type") != value["type"]:
            raise serializers.ValidationError("IP访问控制类型不允许更改")
        return value

    def validate_error_status_code_200(self, value):
        # 后端设置一个固定配置，以通过 validate 中 config 非空检查
        return {"allow": True}

    def validate_type(self, value):
        if self.instance and self.instance.type != value:
            raise serializers.ValidationError("策略类型不允许更改")
        return value

    def to_representation(self, instance):
        # 将 config 赋值给 ip_access_control/rate_limit 属性
        setattr(instance, instance.type, instance.config)
        return super().to_representation(instance)

    def create(self, validated_data):
        validated_data.update(
            {
                "schema": SchemaFactory().get_access_strategy_schema(validated_data["type"]),
            }
        )
        instance = super().create(validated_data)

        request = self.context["request"]
        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.ACCESS_STRATEGY.value,
            op_object_id=instance.id,
            op_object=instance.name,
            comment="创建访问策略",
        )

        return instance

    def update(self, instance, validated_data):
        validated_data.pop("type", None)
        validated_data.pop("created_by", None)

        # 1. 更新数据
        instance = super().update(instance, validated_data)

        # 2. send signal
        reversion_update_signal.send(sender=AccessStrategy, instance_id=instance.id, action="update")

        # 3. 记录操作日志
        request = self.context["request"]
        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.ACCESS_STRATEGY.value,
            op_object_id=instance.id,
            op_object=instance.name,
            comment="更新访问策略",
        )

        return instance


class AccessStrategyListSLZ(serializers.ModelSerializer):
    class Meta:
        model = AccessStrategy
        fields = (
            "id",
            "name",
            "type",
            "comment",
            "created_by",
            "created_time",
            "updated_time",
        )
        read_only_fields = fields
        lookup_field = "id"
