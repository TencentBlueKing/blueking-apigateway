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


@pytest.mark.parametrize("field", ["endpoint", "model_endpoint"])
@pytest.mark.parametrize(
    "url",
    [
        "https://apidemo/component",
        "http://apidemo:8080/v1/chat/completions",
        "https://apidemo.default.svc.cluster.local/component",
        "https://llm.example.com:8443/component?api-version=2026-01-01",
        "http://10.0.0.10:8080/component",
        "http://[fd00::10]:8080/component",
    ],
)
def test_custom_web_endpoints_accept_backend_service_addresses(field, url):
    slz = AIBackendWebInputSLZ(
        data={"provider": "openai-compatible", "endpoint": "https://llm.example.com/component", field: url}
    )

    slz.is_valid(raise_exception=True)

    assert slz.validated_data[field] == url


@pytest.mark.parametrize("field", ["endpoint", "model_endpoint"])
@pytest.mark.parametrize(
    "url, reason",
    [
        ("ftp://llm.example.com/component", "仅支持 HTTP/HTTPS 协议"),
        ("https:///component", "缺少主机名或 IP 地址"),
        ("https://user:secret@llm.example.com/component", "不能包含用户名或密码"),
        ("https://bad_host.example.com/component", "主机名或 IP 格式不合法"),
        ("https://llm.example.com:invalid/component", "端口必须是 1～65535 的整数"),
        ("https://llm.example.com:0/component", "端口必须是 1～65535 的整数"),
        ("https://llm.example.com:65536/component", "端口必须是 1～65535 的整数"),
        ("https://llm.example.com:/component", "端口必须是 1～65535 的整数"),
        ("https://[invalid]/component", "主机名或 IP 格式不合法"),
        ("\x01https://llm.example.com/component", "不能包含空白或控制字符"),
        ("https://llm.exa\nmple.com/component", "不能包含空白或控制字符"),
        ("https://llm.example.com/com ponent", "不能包含空白或控制字符"),
        ("https://llm.example.com/" + "a" * 2048, "URL 长度不能超过 2048 个字符"),
    ],
)
def test_custom_web_endpoints_reject_invalid_urls(field, url, reason):
    slz = AIBackendWebInputSLZ(
        data={"provider": "openai-compatible", "endpoint": "https://llm.example.com/component", field: url}
    )

    assert not slz.is_valid()
    assert reason in str(slz.errors[field][0])
    assert slz.errors[field][0].code == "invalid"
    assert "secret" not in str(slz.errors)


@pytest.mark.parametrize("field", ["endpoint", "model_endpoint"])
@pytest.mark.parametrize(
    "host", ["blocked.example.com", "blocked.example.com:443", "llm.example.com:8443", "llm.example.com:8080"]
)
def test_custom_web_endpoints_reject_forbidden_backend_addresses(settings, field, host):
    settings.FORBIDDEN_HOSTS = ["blocked.example.com", "llm.example.com:8443"]
    settings.FORBIDDEN_PORTS = [8080]
    slz = AIBackendWebInputSLZ(
        data={
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/component",
            field: f"https://{host}/component",
        }
    )

    assert not slz.is_valid()
    assert "该主机或端口不允许使用" in str(slz.errors[field][0])
    assert slz.errors[field][0].code == "invalid"


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
