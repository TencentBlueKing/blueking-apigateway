import copy
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


def test_backend_config_model_masks_plaintext_secrets(ai_backend_config):
    config = AIBackendConfig.model_validate(ai_backend_config)

    assert "encrypt" not in AIBackendConfig.__dict__
    assert "decrypt" not in AIBackendConfig.__dict__
    assert isinstance(config.instances[0], dict)
    assert config.mask().instances[0]["auth"]["header"] == {
        "Authorization": "Be****et",
        "X-Organization": "or****-1",
    }


def test_backend_config_model_uses_private_database_field():
    assert isinstance(BackendConfig.config, property)
    assert BackendConfig._meta.get_field("_config").column == "config"


def test_standard_backend_config_secret_transforms_are_noops():
    data = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com"}],
    }
    config = StandardBackendConfig.model_validate(data)

    assert config.merge() == config
    assert config.mask() == config


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


def test_masked_and_missing_header_keep_existing(ai_backend_config):
    existing = AIBackendConfig.model_validate(ai_backend_config)
    existing_masked = existing.mask()
    masked = copy.deepcopy(ai_backend_config)
    masked["instances"][0]["auth"]["header"] = {
        "Authorization": existing_masked.instances[0]["auth"]["header"]["Authorization"]
    }
    missing = copy.deepcopy(ai_backend_config)
    del missing["instances"][0]["auth"]["header"]

    masked_result = AIBackendConfig.model_validate(masked).merge(existing)
    missing_result = AIBackendConfig.model_validate(missing).merge(existing)

    assert (
        masked_result.instances[0]["auth"]["header"]["Authorization"]
        == existing.instances[0]["auth"]["header"]["Authorization"]
    )
    assert missing_result.instances[0]["auth"]["header"] == existing.instances[0]["auth"]["header"]


def test_short_secret_mask_keeps_existing(ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"] = {"Authorization": "abc"}
    existing = AIBackendConfig.model_validate(ai_backend_config)
    masked = existing.mask()

    result = masked.merge(existing)

    assert result == existing


def test_merge_rejects_short_mask_for_existing_long_secret(ai_backend_config):
    existing = AIBackendConfig.model_validate(ai_backend_config)
    incoming = copy.deepcopy(ai_backend_config)
    incoming["instances"][0]["auth"]["header"]["Authorization"] = "****"

    with pytest.raises(ValueError, match="masked header does not match existing secret"):
        AIBackendConfig.model_validate(incoming).merge(existing)


def test_same_plaintext_does_not_change_ai_backend_config(ai_backend_config):
    existing = AIBackendConfig.model_validate(ai_backend_config)

    assert AIBackendConfig.model_validate(ai_backend_config).merge(existing) == existing


def test_new_plaintext_replaces_existing_secret(ai_backend_config):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["auth"]["header"] = {"X-Api-Key": "new-plaintext"}
    instance["override"] = {"endpoint": "https://example.com/v1"}
    existing = copy.deepcopy(ai_backend_config)
    existing["instances"][0]["auth"]["header"]["X-Api-Key"] = "old-plaintext"

    result = AIBackendConfig.model_validate(ai_backend_config).merge(existing)

    assert result.instances[0]["auth"]["header"]["X-Api-Key"] == "new-plaintext"


def test_merge_explicit_empty_header_clears_existing(ai_backend_config):
    existing = AIBackendConfig.model_validate(ai_backend_config)
    incoming = copy.deepcopy(ai_backend_config)
    incoming["instances"][0]["auth"]["header"] = {}

    with pytest.raises(ValueError, match="Authorization header is required"):
        AIBackendConfig.model_validate(incoming).merge(existing)


def test_model_rejects_case_insensitive_duplicate_headers(ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"]["authorization"] = "duplicate"

    with pytest.raises(ValueError, match="duplicate header"):
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
    if auth is None:
        instance.pop("auth")
    else:
        instance["auth"] = auth

    stored = AIBackendConfig.model_validate(ai_backend_config).merge().to_config()

    assert stored["instances"][0].get("auth") == expected


@pytest.mark.parametrize(
    ("provider", "override", "error"),
    [
        ("openai", {"endpoint": "https://example.com/v1"}, "override is not allowed"),
        ("openai-compatible", None, "override.endpoint is required"),
    ],
)
def test_merge_validates_provider_contract(ai_backend_config, provider, override, error):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = provider
    if override is None:
        instance.pop("override", None)
    else:
        instance["override"] = override

    with pytest.raises(ValueError, match=error):
        AIBackendConfig.model_validate(ai_backend_config).merge()


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


@pytest.mark.parametrize(
    ("secret", "expected"),
    [("abc", "****"), ("abcd", "ab****cd"), ("abcdef", "ab****ef")],
)
def test_mask_preserves_two_characters_at_each_end(ai_backend_config, secret, expected):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = "openai-compatible"
    instance["auth"]["header"] = {"X-Api-Key": secret}
    instance["override"] = {"endpoint": "https://example.com/v1"}
    masked = AIBackendConfig.model_validate(ai_backend_config).mask()

    assert masked.instances[0]["auth"]["header"]["X-Api-Key"] == expected


def test_standard_config_is_validated_without_secret_processing():
    config = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com"}],
    }

    model = StandardBackendConfig.model_validate(config)
    assert model.merge().to_config() == config
    assert model.mask().to_config() == config
