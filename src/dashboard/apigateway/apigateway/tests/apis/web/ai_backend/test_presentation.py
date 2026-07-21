import logging
from types import SimpleNamespace

import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.ai_backend import serialize_ai_backend_config_for_web


def test_serialize_ai_backend_config_for_web():
    backend_config = SimpleNamespace(
        id=42,
        config={
            "timeout": 300,
            "instances": [
                {
                    "name": "primary",
                    "provider": "openai",
                    "auth": {"header": {"Authorization": "Bearer secret"}},
                }
            ],
        },
    )

    assert serialize_ai_backend_config_for_web(backend_config) == {
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model_endpoint": "https://api.openai.com/v1/models",
        "api_key": "se****et",
        "auth_header": None,
        "model": None,
        "model_options": {},
        "timeout": 300,
    }


@pytest.mark.parametrize(
    "config",
    [
        {"instances": []},
        {
            "instances": [
                {
                    "name": "primary",
                    "provider": "openai-compatible",
                    "auth": {"header": {"X-Api-Key": "secret", "X-Tenant": "tenant"}},
                    "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
                }
            ]
        },
    ],
)
def test_serialize_ai_backend_config_for_web_maps_expected_errors(config, caplog):
    backend_config = SimpleNamespace(id=42, config=config)

    with caplog.at_level(logging.ERROR), pytest.raises(ValidationError) as exc_info:
        serialize_ai_backend_config_for_web(backend_config, error_field="configs")

    assert str(exc_info.value.detail["configs"]) == "已有模型服务配置无法通过 Web 接口编辑。"
    assert "backend_config_id=42" in caplog.text
