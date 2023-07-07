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
import re
from typing import Dict

from blue_krill.data_types.enum import EnumField, StructuredEnum

from apigateway.common.constants import ChoiceEnum
from apigateway.core.constants import ScopeTypeEnum


class IPAccessControlTypeEnum(ChoiceEnum):
    ALLOW = "allow"
    DENY = "deny"


class AccessStrategyTypeEnum(StructuredEnum):
    IP_ACCESS_CONTROL = EnumField("ip_access_control", label="IP访问控制")
    RATE_LIMIT = EnumField("rate_limit", label="频率控制")
    USER_VERIFIED_UNREQUIRED_APPS = EnumField("user_verified_unrequired_apps", label="免用户认证应用白名单")
    ERROR_STATUS_CODE_200 = EnumField("error_status_code_200", label="网关错误使用HTTP状态码200(不推荐)")
    CORS = EnumField("cors", label="跨域资源共享(CORS)")
    CIRCUIT_BREAKER = EnumField("circuit_breaker", label="断路器")


# 访问策略类型 -> 插件类型，用于二者类型的转换
STRATEGY_TYPE_TO_PLUGIN_TYPE: Dict[str, str] = {
    AccessStrategyTypeEnum.IP_ACCESS_CONTROL.value: "bk-ip-restriction",
    AccessStrategyTypeEnum.RATE_LIMIT.value: "bk-rate-limit",
    AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value: "bk-verified-user-exempted-apps",
    AccessStrategyTypeEnum.ERROR_STATUS_CODE_200.value: "bk-status-rewrite",
    AccessStrategyTypeEnum.CORS.value: "bk-cors",
}

# 插件类型 -> 访问策略类型
PLUGIN_TYPE_TO_STRATEGY_TYPE: Dict[str, str] = {value: key for key, value in STRATEGY_TYPE_TO_PLUGIN_TYPE.items()}


class AccessStrategyBindScopeEnum(ChoiceEnum):
    STAGE = ScopeTypeEnum.STAGE.value
    RESOURCE = ScopeTypeEnum.RESOURCE.value


class CircuitBreakerStrategyTypeEnum(ChoiceEnum):
    # CONSECUTIVE_FAIL = "consecutive_fail"
    THRESHOLD = "threshold"
    # FAILURES_RATE = "failures_rate"


class CircuitBreakerBackOffTypeEnum(ChoiceEnum):
    FIXED = "fixed"
    # EXPONENTIAL = "exponential"


# `:[]` 用于支持 ipv6
ALLOWED_ORIGIN_PATTERN = re.compile(r"^\*$|^http(s)?://[-a-zA-Z0-9:\[\]\*\.]+(:(\d+|\*))?$")
