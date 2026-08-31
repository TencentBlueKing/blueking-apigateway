import logging

import pytest

from apigateway.biz.backend.connectivity import (
    AIBackendConnectivityError,
    AIBackendEndpointError,
    AIBackendModelEndpointRequiredError,
    _derive_models_endpoint,
    _resolve_endpoint,
    get_ai_backend_model_ids,
)


def _config(provider="openai", **instance_values):
    instance = {
        "name": "primary",
        "provider": provider,
        "weight": 0,
        "auth": {"header": {"Authorization": "Bearer secret"}},
        **instance_values,
    }
    return {"timeout": 300, "instances": [instance]}


@pytest.mark.parametrize(
    ("completion", "models"),
    [
        ("https://llm.example.com/v1/chat/completions", "https://llm.example.com/v1/models"),
        ("https://llm.example.com/chat/completions", "https://llm.example.com/models"),
        (
            "https://llm.example.com/v1/chat/completions?api-version=2026-01-01#fragment",
            "https://llm.example.com/v1/models?api-version=2026-01-01",
        ),
    ],
)
def test_derive_models_endpoint(completion, models):
    assert _derive_models_endpoint(completion) == models


def test_non_derivable_endpoint_requires_explicit_model_endpoint():
    with pytest.raises(AIBackendModelEndpointRequiredError):
        _derive_models_endpoint("https://llm.example.com/v1/generate")


def test_inferred_models_failure_does_not_fallback(mocker):
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    http_get = mocker.patch("apigateway.biz.backend.connectivity.http_get", return_value=(False, {}))
    config = _config(
        "openai-compatible",
        override={"endpoint": "https://llm.example.com/v1/chat/completions"},
    )

    with pytest.raises(AIBackendModelEndpointRequiredError):
        get_ai_backend_model_ids(config)

    assert http_get.call_count == 1
    assert http_get.call_args.args[0] == "https://llm.example.com/v1/models"


def test_explicit_models_endpoint_may_use_different_origin(mocker):
    resolver = mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    http_get = mocker.patch(
        "apigateway.biz.backend.connectivity.http_get",
        return_value=(True, {"data": [{"id": "model-a"}]}),
    )
    config = _config(
        "openai-compatible",
        override={"endpoint": "https://chat.example.com/v1/chat/completions"},
        model_endpoint="https://catalog.example.net/models",
    )

    assert get_ai_backend_model_ids(config) == ["model-a"]
    assert [call.args[0] for call in resolver.call_args_list] == [
        "https://chat.example.com/v1/chat/completions",
        "https://catalog.example.net/models",
    ]
    assert http_get.call_args.args[0] == "https://catalog.example.net/models"


@pytest.mark.parametrize(
    ("provider", "expected_url"),
    [
        ("openai", "https://api.openai.com/v1/models"),
        ("deepseek", "https://api.deepseek.com/models"),
    ],
)
def test_builtin_provider_uses_registry_models_endpoint(mocker, provider, expected_url):
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    http_get = mocker.patch(
        "apigateway.biz.backend.connectivity.http_get",
        return_value=(True, {"data": [{"id": "model-a"}]}),
    )

    assert get_ai_backend_model_ids(_config(provider)) == ["model-a"]
    assert http_get.call_args.args[0] == expected_url


def test_rejects_forbidden_resolved_address(mocker):
    mocker.patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("169.254.169.254", 443))])

    with pytest.raises(AIBackendEndpointError):
        _resolve_endpoint("https://models.example.com/v1/models")


def test_provider_redirect_is_rejected(mocker):
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    mocker.patch("apigateway.biz.backend.connectivity.http_get", return_value=(False, {"status_code": 302}))

    with pytest.raises(AIBackendConnectivityError):
        get_ai_backend_model_ids(_config())


def test_rejects_malformed_provider_response(mocker):
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    mocker.patch(
        "apigateway.biz.backend.connectivity.http_get",
        return_value=(True, {"data": [{"name": "missing-id"}]}),
    )

    with pytest.raises(AIBackendConnectivityError):
        get_ai_backend_model_ids(_config())


def test_provider_failure_log_does_not_expose_credentials(caplog, mocker):
    mocker.patch("apigateway.biz.backend.connectivity._resolve_endpoint")
    mocker.patch(
        "apigateway.biz.backend.connectivity.http_get",
        return_value=(False, {"error": "Authorization: Bearer secret"}),
    )

    with caplog.at_level(logging.WARNING), pytest.raises(AIBackendConnectivityError):
        get_ai_backend_model_ids(_config())

    assert "Bearer secret" not in caplog.text
    assert "Authorization" not in caplog.text
