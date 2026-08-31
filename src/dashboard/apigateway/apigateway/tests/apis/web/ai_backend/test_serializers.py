import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.ai_backend import AIBackendWebInputSLZ


def test_builtin_web_input_uses_registry_and_optional_model():
    slz = AIBackendWebInputSLZ(data={"provider": "openai", "api_key": "secret"})

    slz.is_valid(raise_exception=True)

    assert slz.validated_data == {
        "provider": "openai",
        "api_key": "secret",
        "model_options": {},
        "timeout": 300,
    }


@pytest.mark.parametrize("field", ["instances", "auth", "override", "balancer", "fallback_strategy"])
def test_web_input_rejects_internal_fields(field):
    slz = AIBackendWebInputSLZ(data={"provider": "openai", "api_key": "secret", field: {}})

    with pytest.raises(ValidationError):
        slz.is_valid(raise_exception=True)


def test_custom_web_input_accepts_optional_auth_model_and_models_endpoint():
    slz = AIBackendWebInputSLZ(
        data={
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/v1/chat/completions",
        }
    )

    slz.is_valid(raise_exception=True)

    assert slz.validated_data == {
        "provider": "openai-compatible",
        "endpoint": "https://llm.example.com/v1/chat/completions",
        "model_options": {},
        "timeout": 300,
    }


def test_custom_web_input_rejects_model_inside_model_options():
    slz = AIBackendWebInputSLZ(
        data={
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/v1/chat/completions",
            "model_options": {"model": "duplicate"},
        }
    )

    assert not slz.is_valid()
    assert "model_options" in slz.errors


def test_builtin_web_input_rejects_registry_endpoint_override():
    slz = AIBackendWebInputSLZ(
        data={"provider": "openai", "endpoint": "https://other.example.com/v1", "api_key": "secret"}
    )

    assert not slz.is_valid()
    assert "endpoint" in slz.errors


def test_builtin_web_input_accepts_read_only_registry_endpoints_on_round_trip():
    slz = AIBackendWebInputSLZ(
        data={
            "provider": "openai",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model_endpoint": "https://api.openai.com/v1/models",
            "api_key": "se****et",
        }
    )

    slz.is_valid(raise_exception=True)

    assert slz.validated_data["endpoint"] == "https://api.openai.com/v1/chat/completions"
    assert slz.validated_data["model_endpoint"] == "https://api.openai.com/v1/models"


@pytest.mark.parametrize("timeout", [0, 301])
def test_web_input_rejects_timeout_outside_seconds_range(timeout):
    slz = AIBackendWebInputSLZ(data={"provider": "openai", "api_key": "secret", "timeout": timeout})

    assert not slz.is_valid()
    assert "timeout" in slz.errors
