from copy import deepcopy

import pytest
from django.utils.translation import override
from rest_framework.exceptions import ValidationError

from apigateway.apis.backend_config import validate_ai_backend_config


@pytest.mark.parametrize(
    "change, field, message",
    [
        ("duplicate_name", "instances", "模型实例名称不能重复。"),
        ("priority", "instances", "模型实例优先级只能为 10（主实例）或 0（备用实例）。"),
        ("no_primary", "instances", "至少需要一个主实例，且最多只能配置一个备用实例。"),
        ("two_backups", "instances", "至少需要一个主实例，且最多只能配置一个备用实例。"),
        ("weight", "instances", "多实例配置的权重必须为 1。"),
        ("null_strategy", "fallback_strategy", "故障重试策略必须为数组。"),
        ("empty_strategy", "fallback_strategy", "配置备用实例时，至少需要启用一项故障重试条件。"),
        ("unsupported_strategy", "fallback_strategy", "故障重试策略仅支持 http_429 和 http_5xx 数组。"),
        ("custom_hash", "balancer", "一致性哈希仅支持 vars_combinations 和 $bk_app_code。"),
        ("roundrobin_hash", "balancer", "轮询算法不支持配置 hash_on 和 key。"),
    ],
)
def test_ai_pool_rule_errors_keep_field_and_translatable_message(change, field, message):
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

    with override("zh-cn"), pytest.raises(ValidationError) as err:
        validate_ai_backend_config(config)
    assert err.value.detail == {field: [message]}


def test_ai_pool_rule_error_uses_request_language():
    instance = {"name": "same", "provider": "openai", "auth": {"header": {"Authorization": "Bearer key"}}}
    with override("en"), pytest.raises(ValidationError) as err:
        validate_ai_backend_config({"instances": [instance, deepcopy(instance)]})
    assert err.value.detail == {"instances": ["Model instance names must be unique."]}
