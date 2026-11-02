# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from copy import deepcopy

import pytest
from django.utils.translation import override

from apigateway.apis.backend_config import validate_ai_backend_config
from apigateway.common.error_codes import APIError


@pytest.mark.parametrize(
    "change, message",
    [
        ("duplicate_name", "模型实例名称不能重复。"),
        ("priority", "模型实例优先级只能为 10（主实例）或 0（备用实例）。"),
        ("no_primary", "至少需要一个主实例，且最多只能配置一个备用实例。"),
        ("two_backups", "至少需要一个主实例，且最多只能配置一个备用实例。"),
        ("weight", "多实例配置的权重必须为 1。"),
        ("null_strategy", "故障重试策略必须为数组。"),
        ("empty_strategy", "配置备用实例时，至少需要启用一项故障重试条件。"),
        ("unsupported_strategy", "故障重试策略仅支持 http_429 和 http_5xx 数组。"),
        ("custom_hash", "一致性哈希仅支持 vars_combinations 和 $bk_app_code。"),
        ("roundrobin_hash", "轮询算法不支持配置 hash_on 和 key。"),
    ],
)
def test_ai_pool_rule_errors_use_standard_error_code(change, message):
    config = {
        "instances": [
            {"name": "primary", "provider": "openai", "auth": {"header": {"Authorization": "Bearer key"}}},
            {
                "name": "backup",
                "priority": 0,
                "provider": "openai",
                "auth": {"header": {"Authorization": "Bearer other-key"}},
            },
        ]
    }
    if change == "duplicate_name":
        config["instances"][1]["name"] = "primary"
    elif change == "priority":
        config["instances"][0]["priority"] = 5
    elif change == "no_primary":
        config["instances"][0]["priority"] = 0
    elif change == "two_backups":
        extra = deepcopy(config["instances"][1])
        extra["name"] = "other-backup"
        config["instances"].append(extra)
    elif change == "weight":
        config["instances"][0]["weight"] = 2
    elif change == "null_strategy":
        config["fallback_strategy"] = None
    elif change == "empty_strategy":
        config["fallback_strategy"] = []
    elif change == "unsupported_strategy":
        config["fallback_strategy"] = ["rate_limiting"]
    elif change == "custom_hash":
        config["balancer"] = {"algorithm": "chash", "hash_on": "vars_combinations", "key": "$other"}
    elif change == "roundrobin_hash":
        config["balancer"] = {"algorithm": "roundrobin", "hash_on": "vars", "key": "other"}

    with override("zh-cn"), pytest.raises(APIError) as err:
        validate_ai_backend_config(config)
    assert err.value.code.code_name == "INVALID_ARGUMENT"
    assert err.value.code.status_code == 400
    assert str(err.value.code.message).endswith(message)


def test_ai_pool_rule_error_uses_request_language():
    instance = {"name": "same", "provider": "openai", "auth": {"header": {"Authorization": "Bearer key"}}}
    with override("en"), pytest.raises(APIError) as err:
        validate_ai_backend_config({"instances": [instance, deepcopy(instance)]})
    assert str(err.value.code.message).endswith("Model instance names must be unique.")
