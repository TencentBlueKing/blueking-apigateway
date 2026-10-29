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

from apigateway.apis.backend_config import validate_ai_backend_config
from apigateway.common.error_codes import APIError
from apigateway.core.backend_config import AIBackendConfig, get_ai_pool_routing_error


def instance(name, **kwargs):
    return {
        "name": name,
        "provider": "openai-compatible",
        "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
        **kwargs,
    }


def test_write_defaults_pool_without_mutating_input():
    data = {"instances": [instance("b"), instance("a")]}
    original = deepcopy(data)

    config = validate_ai_backend_config(data)

    assert data == original
    assert config == {
        "timeout": 300,
        "instances": [instance("a", priority=10, weight=1), instance("b", priority=10, weight=1)],
        "balancer": {"algorithm": "roundrobin"},
        "fallback_strategy": ["http_429", "http_5xx"],
    }
    assert validate_ai_backend_config(config) == config


def test_write_chash_fills_fixed_application_key_and_keeps_retry_disabled():
    config = validate_ai_backend_config(
        {
            "instances": [instance("a"), instance("b")],
            "balancer": {"algorithm": "chash"},
            "fallback_strategy": [],
        }
    )
    assert config["balancer"] == {"algorithm": "chash", "hash_on": "vars_combinations", "key": "$bk_app_code"}
    assert config["fallback_strategy"] == []


def test_write_backup_and_retry_normalization():
    config = validate_ai_backend_config(
        {
            "instances": [instance("b", priority=0), instance("a", priority=10)],
            "fallback_strategy": ["http_5xx", "http_429", "http_5xx"],
        }
    )
    assert config["fallback_strategy"] == ["http_429", "http_5xx"]
    assert [(item["name"], item["priority"], item["weight"]) for item in config["instances"]] == [
        ("a", 10, 1),
        ("b", 0, 1),
    ]


@pytest.mark.parametrize(
    "patch",
    [
        {"instances": [instance("a"), instance("a")]},
        {"instances": [instance("a", priority=0)]},
        {"instances": [instance("a", priority=0), instance("b", priority=0)]},
        {"instances": [instance("a"), instance("b", priority=5)]},
        {"instances": [instance("a", weight=0), instance("b")]},
        {"instances": [instance("a"), instance("b", priority=0)], "fallback_strategy": []},
        {"fallback_strategy": ["rate_limiting"]},
        {"fallback_strategy": "http_429"},
        {"fallback_strategy": None},
        {"balancer": {"algorithm": "chash", "hash_on": "consumer"}},
        {"balancer": {"algorithm": "chash", "key": "$remote_addr"}},
        {"balancer": {"algorithm": "roundrobin", "key": "$bk_app_code"}},
    ],
)
def test_write_rejects_unsupported_pool(patch):
    with pytest.raises(APIError) as err:
        validate_ai_backend_config({"instances": [instance("a"), instance("b")], **patch})
    assert err.value.code.code_name == "INVALID_ARGUMENT"
    assert err.value.code.status_code == 400


def test_historical_parse_does_not_enable_retries_or_rewrite_weights():
    data = {"timeout": 60, "instances": [instance("a", weight=0), instance("b", weight=0)]}
    assert AIBackendConfig.model_validate(data).to_config() == data


def test_single_instance_accepts_empty_strategy_without_enabling_routing():
    config = validate_ai_backend_config({"instances": [instance("a")], "fallback_strategy": []})
    assert config == {"timeout": 300, "instances": [instance("a", weight=0)]}


def test_empty_balancer_uses_roundrobin_default():
    config = validate_ai_backend_config({"instances": [instance("a"), instance("b")], "balancer": {}})
    assert config["balancer"] == {"algorithm": "roundrobin"}


@pytest.mark.parametrize(
    "balancer",
    [
        {"algorithm": "roundrobin", "hash_on": "vars_combinations"},
        {"algorithm": "roundrobin", "key": "$bk_app_code"},
        {"algorithm": "roundrobin", "hash_on": "vars_combinations", "key": "$bk_app_code"},
        {"key": "$bk_app_code"},
    ],
)
def test_roundrobin_hash_fields_are_rejected_by_shared_read_check_and_write_validation(balancer):
    config = {"instances": [instance("a"), instance("b")], "balancer": balancer}
    before = deepcopy(config)

    assert get_ai_pool_routing_error(AIBackendConfig.model_validate(config).to_config()) is not None
    with pytest.raises(APIError) as err:
        validate_ai_backend_config(config)
    assert err.value.code.code_name == "INVALID_ARGUMENT"
    assert config == before
