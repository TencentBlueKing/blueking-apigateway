import json

import pytest
from django.db import connection
from django_dynamic_fixture import G

from apigateway.core.backend_config import AIBackendConfig, StandardBackendConfig
from apigateway.core.constants import BackendKindEnum
from apigateway.core.models import Backend, BackendConfig


@pytest.fixture
def ai_backend_config():
    return {
        "timeout": 30000,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer secret", "X-Organization": "org-1"}},
                "options": {"model": "gpt-4o"},
            }
        ],
    }


@pytest.fixture
def ai_backend(fake_stage):
    return G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value)


def test_backend_config_model_uses_private_database_field():
    assert isinstance(BackendConfig.config, property)
    assert BackendConfig._meta.get_field("_config").column == "config"


def test_backend_config_model_encrypts_entire_ai_config_at_storage_boundary(fake_stage, ai_backend, ai_backend_config):
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=ai_backend,
        stage=fake_stage,
        config=ai_backend_config,
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT config FROM core_backend_config WHERE id = %s", [backend_config.pk])
        stored_config = json.loads(cursor.fetchone()[0])

    assert set(stored_config) == {"encrypted"}
    assert isinstance(stored_config["encrypted"], str)
    assert "primary" not in json.dumps(stored_config)
    assert "Bearer secret" not in json.dumps(stored_config)
    assert BackendConfig.objects.get(pk=backend_config.pk).config == ai_backend_config


def test_backend_config_model_masks_ai_config_for_display(fake_stage, ai_backend, ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"]["X-Organization"] = "abc"
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=ai_backend,
        stage=fake_stage,
        config=ai_backend_config,
    )

    display_config = BackendConfig.objects.get(pk=backend_config.pk).get_config_for_display()

    assert display_config["instances"][0]["auth"]["header"] == {
        "Authorization": "Be****et",
        "X-Organization": "****",
    }
    assert display_config["instances"][0]["name"] == "primary"
    assert backend_config.config == ai_backend_config


@pytest.mark.parametrize(
    ("secret", "expected"),
    [
        ("abc", "****"),
        ("abcd", "ab****cd"),
        ("abcde", "ab****de"),
        ("abcdefgh", "ab****gh"),
        ("a" * 100, f"aa****{'a' * 2}"),
    ],
)
def test_backend_config_model_masks_header_value_by_length(
    fake_stage, ai_backend, ai_backend_config, secret, expected
):
    ai_backend_config["instances"][0]["auth"]["header"] = {"Authorization": secret}
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=ai_backend,
        stage=fake_stage,
        config=ai_backend_config,
    )

    display_config = backend_config.get_config_for_display()

    assert display_config["instances"][0]["auth"]["header"]["Authorization"] == expected


def test_backend_config_model_keeps_standard_config_plaintext(fake_stage):
    standard_config = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com"}],
    }
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.STANDARD.value)
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=backend,
        stage=fake_stage,
        config=standard_config,
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT config FROM core_backend_config WHERE id = %s", [backend_config.pk])
        stored_config = json.loads(cursor.fetchone()[0])

    assert stored_config == standard_config
    assert BackendConfig.objects.get(pk=backend_config.pk).config == standard_config
    assert BackendConfig.objects.get(pk=backend_config.pk).get_config_for_display() == standard_config


def test_backend_config_model_uses_backend_kind_for_secret_processing(fake_stage, ai_backend_config):
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.STANDARD.value)
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=backend,
        stage=fake_stage,
        config=ai_backend_config,
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT config FROM core_backend_config WHERE id = %s", [backend_config.pk])
        stored_config = json.loads(cursor.fetchone()[0])

    assert stored_config == ai_backend_config
    assert BackendConfig.objects.get(pk=backend_config.pk).config == ai_backend_config


def test_backend_config_model_reads_legacy_standard_config(fake_stage):
    standard_config = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "legacy.example.com"}],
    }
    backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.STANDARD.value)
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=backend,
        stage=fake_stage,
        config={},
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE core_backend_config SET config = %s WHERE id = %s",
            [json.dumps(standard_config), backend_config.pk],
        )

    assert BackendConfig.objects.get(pk=backend_config.pk).config == standard_config


def test_ai_backend_config_rejects_empty_required_header(ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"] = {}

    with pytest.raises(ValueError, match="Authorization header is required"):
        AIBackendConfig.model_validate(ai_backend_config)


def test_model_rejects_case_insensitive_duplicate_headers(ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"]["authorization"] = "duplicate"

    with pytest.raises(ValueError, match="duplicate header"):
        AIBackendConfig.model_validate(ai_backend_config)


@pytest.mark.parametrize("header", ["Host", "content-length", "TRANSFER-ENCODING", "Connection"])
def test_ai_backend_config_rejects_forbidden_headers(ai_backend_config, header):
    ai_backend_config["instances"][0]["auth"]["header"][header] = "value"

    with pytest.raises(ValueError, match=f"header is forbidden: {header}"):
        AIBackendConfig.model_validate(ai_backend_config)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("instances", 0, "model_endpoint"), "https://{{env.host}}/models"),
        (("instances", 0, "name"), "{env.instance_name}"),
        (("instances", 0, "auth", "header", "Authorization"), "Bearer {{env.token}}"),
        (("instances", 0, "options", "model"), "{env.model}"),
        (("instances", 0, "options", "metadata"), {"region": "{{env.region}}"}),
    ],
)
def test_ai_backend_config_rejects_environment_variables(ai_backend_config, path, value):
    target = ai_backend_config
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(ValueError, match="must not contain environment variables"):
        AIBackendConfig.model_validate(ai_backend_config)


def test_ai_backend_config_rejects_environment_variables_in_header_names(ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"]["{{env.header_name}}"] = "value"

    with pytest.raises(ValueError, match="must not contain environment variables"):
        AIBackendConfig.model_validate(ai_backend_config)


@pytest.mark.parametrize("patch", [{"instances": []}, {"unknown": True}, {"timeout": 0}])
def test_ai_backend_config_rejects_invalid_top_level(ai_backend_config, patch):
    with pytest.raises(ValueError):
        AIBackendConfig.model_validate(ai_backend_config | patch)


def test_ai_backend_config_preserves_additional_json_options(ai_backend_config):
    ai_backend_config["instances"][0]["options"].update(
        {"temperature": 0.7, "stream": True, "metadata": {"tags": ["production", None]}}
    )

    config = AIBackendConfig.model_validate(ai_backend_config)

    assert config.to_config() == ai_backend_config


def test_ai_backend_config_defaults_optional_instance_fields(ai_backend_config):
    ai_backend_config.pop("timeout")
    instance = ai_backend_config["instances"][0]
    instance.pop("weight")
    instance["options"] = {}

    stored = AIBackendConfig.model_validate(ai_backend_config).to_config()

    assert stored["timeout"] == 30
    assert stored["instances"][0]["weight"] == 0
    assert stored["instances"][0]["options"] == {}


def test_backend_config_optional_fields_reject_explicit_null(ai_backend_config):
    ai_backend_config["instances"][0]["auth"] = None
    standard_backend_config = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com", "weight": None}],
    }

    with pytest.raises(ValueError):
        AIBackendConfig.model_validate(ai_backend_config)
    with pytest.raises(ValueError):
        StandardBackendConfig.model_validate(standard_backend_config)


@pytest.mark.parametrize(
    ("auth", "expected"),
    [
        (None, None),
        ({}, {}),
        ({"header": {}}, {"header": {}}),
    ],
)
def test_ai_backend_config_preserves_empty_auth_shape(ai_backend_config, auth, expected):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["override"] = {"endpoint": "https://example.com/v1"}
    instance["model_endpoint"] = "https://example.com/models"
    if auth is None:
        instance.pop("auth")
    else:
        instance["auth"] = auth

    stored = AIBackendConfig.model_validate(ai_backend_config).to_config()

    assert stored["instances"][0].get("auth") == expected


@pytest.mark.parametrize(
    ("provider", "override", "error"),
    [
        ("openai", {"endpoint": "https://example.com/v1"}, "override is not allowed"),
        ("openai-compatible", None, "override.endpoint is required"),
    ],
)
def test_ai_backend_config_validates_provider_contract(ai_backend_config, provider, override, error):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = provider
    if override is None:
        instance.pop("override", None)
    else:
        instance["override"] = override

    with pytest.raises(ValueError, match=error):
        AIBackendConfig.model_validate(ai_backend_config)


def test_model_rejects_plaintext_in_private_storage(fake_stage, ai_backend, ai_backend_config):
    backend_config = BackendConfig.objects.create(
        gateway=fake_stage.gateway,
        backend=ai_backend,
        stage=fake_stage,
        config=ai_backend_config,
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE core_backend_config SET config = %s WHERE id = %s",
            [json.dumps(ai_backend_config), backend_config.pk],
        )

    with pytest.raises(ValueError, match="failed to decrypt"):
        _ = BackendConfig.objects.get(pk=backend_config.pk).config


def test_standard_config_is_validated_without_secret_processing():
    config = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com"}],
    }

    model = StandardBackendConfig.model_validate(config)
    assert model.to_config() == config


@pytest.mark.parametrize(
    ("endpoint", "error"),
    [
        ("ftp://example.com/v1", "scheme must be http or https"),
        ("https://", "hostname is required"),
        ("https://user:pass@example.com/v1", "userinfo is not allowed"),
        ("https://127.0.0.1/v1", "host is forbidden"),
    ],
)
def test_ai_backend_config_validates_override_endpoint(ai_backend_config, endpoint, error):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["override"] = {"endpoint": endpoint}
    instance["model_endpoint"] = "https://example.com/models"

    with pytest.raises(ValueError, match=error):
        AIBackendConfig.model_validate(ai_backend_config)


def test_ai_backend_config_rejects_forbidden_override_endpoint_port(ai_backend_config, settings):
    settings.FORBIDDEN_PORTS = [22]
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["override"] = {"endpoint": "https://example.com:22/v1"}
    instance["model_endpoint"] = "https://example.com/models"

    with pytest.raises(ValueError, match="port is forbidden"):
        AIBackendConfig.model_validate(ai_backend_config)


def test_ai_backend_config_accepts_legacy_openai_compatible_without_model_endpoint(ai_backend_config):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["override"] = {"endpoint": "https://example.com/v1"}

    stored = AIBackendConfig.model_validate(ai_backend_config).to_config()

    assert "model_endpoint" not in stored["instances"][0]


def test_ai_backend_config_rejects_forbidden_model_endpoint_port(ai_backend_config, settings):
    settings.FORBIDDEN_PORTS = [22]
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["override"] = {"endpoint": "https://example.com/v1"}
    instance["model_endpoint"] = "https://example.com:22/models"

    with pytest.raises(ValueError, match="port is forbidden"):
        AIBackendConfig.model_validate(ai_backend_config)
