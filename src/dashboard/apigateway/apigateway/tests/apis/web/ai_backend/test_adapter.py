import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.ai_backend import AIBackendWebConfigAdapter, AIBackendWebConfigNotRepresentable


def test_adapter_maps_builtin_form_to_storage_and_back():
    stored = AIBackendWebConfigAdapter.to_internal(
        {"provider": "openai", "api_key": "secret", "model_options": {}, "timeout": 300}
    )

    assert stored["instances"] == [
        {
            "name": "primary",
            "provider": "openai",
            "weight": 0,
            "auth": {"header": {"Authorization": "Bearer secret"}},
            "options": {},
        }
    ]
    assert AIBackendWebConfigAdapter.to_web(stored) == {
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model_endpoint": "https://api.openai.com/v1/models",
        "api_key": "se****et",
        "auth_header": None,
        "model": None,
        "model_options": {},
        "timeout": 300,
    }


def test_adapter_maps_optional_custom_form_to_storage_and_back():
    stored = AIBackendWebConfigAdapter.to_internal(
        {
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/v1/chat/completions",
            "model_options": {},
            "timeout": 300,
        }
    )

    assert stored["instances"] == [
        {
            "name": "primary",
            "provider": "openai-compatible",
            "weight": 0,
            "options": {},
            "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
        }
    ]
    assert AIBackendWebConfigAdapter.to_web(stored)["auth_header"] is None
    assert AIBackendWebConfigAdapter.to_web(stored)["model_endpoint"] is None


def test_adapter_preserves_exact_mask_only_for_same_destination():
    existing = AIBackendWebConfigAdapter.to_internal(
        {
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/v1/chat/completions",
            "auth_header": {"name": "X-Api-Key", "value": "secret"},
            "model_options": {},
            "timeout": 300,
        }
    )
    masked = AIBackendWebConfigAdapter.to_web(existing)

    restored = AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)

    assert restored["instances"][0]["auth"] == {"header": {"X-Api-Key": "secret"}}


def test_adapter_rejects_masked_credential_after_destination_change():
    existing = AIBackendWebConfigAdapter.to_internal(
        {
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/v1/chat/completions",
            "auth_header": {"name": "X-Api-Key", "value": "secret"},
            "model_options": {},
            "timeout": 300,
        }
    )
    masked = AIBackendWebConfigAdapter.to_web(existing)
    masked["endpoint"] = "https://other.example.com/v1/chat/completions"

    with pytest.raises(ValidationError, match="重新输入"):
        AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)


def test_adapter_rejects_masked_credential_after_header_name_change():
    existing = AIBackendWebConfigAdapter.to_internal(
        {
            "provider": "openai-compatible",
            "endpoint": "https://llm.example.com/v1/chat/completions",
            "auth_header": {"name": "X-Api-Key", "value": "secret"},
            "model_options": {},
            "timeout": 300,
        }
    )
    masked = AIBackendWebConfigAdapter.to_web(existing)
    masked["auth_header"]["name"] = "X-Other-Key"

    with pytest.raises(ValidationError, match="重新输入"):
        AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)


def test_adapter_fails_closed_when_storage_has_multiple_headers():
    config = {
        "timeout": 300,
        "instances": [
            {
                "name": "primary",
                "provider": "openai-compatible",
                "weight": 0,
                "auth": {"header": {"X-Api-Key": "secret", "X-Tenant": "tenant"}},
                "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
            }
        ],
    }

    with pytest.raises(AIBackendWebConfigNotRepresentable, match="multiple auth headers"):
        AIBackendWebConfigAdapter.to_web(config)


def test_adapter_fails_closed_when_storage_has_multiple_instances():
    instance = {
        "name": "primary",
        "provider": "openai-compatible",
        "weight": 0,
        "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
    }
    config = {"timeout": 300, "instances": [instance, {**instance, "name": "secondary"}]}

    with pytest.raises(AIBackendWebConfigNotRepresentable, match="exactly one instance"):
        AIBackendWebConfigAdapter.to_web(config)


def _pool_form():
    return {
        "timeout": 60,
        "balancer": {"algorithm": "chash"},
        "instances": [
            {"name": "a", "provider": "openai", "api_key": "alpha-secret"},
            {
                "name": "b",
                "priority": 0,
                "provider": "openai-compatible",
                "endpoint": "https://backup.example.com/v1/chat/completions",
                "auth_header": {"name": "X-Key", "value": "beta-secret"},
            },
        ],
    }


def test_pool_roundtrip_keeps_credentials_by_name_when_reordered():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    masked = AIBackendWebConfigAdapter.to_web(existing, config_format="instances")
    assert masked["balancer"] == {"algorithm": "chash"}
    assert masked["instances"][0]["api_key"] == "al****et"
    masked["instances"].reverse()
    assert AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing) == existing


def test_legacy_form_cannot_replace_pool():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    with pytest.raises(ValidationError):
        AIBackendWebConfigAdapter.to_internal(
            {"provider": "openai", "api_key": "new-secret"}, existing_config=existing
        )


def test_pool_changed_destination_requires_new_secret():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    masked = AIBackendWebConfigAdapter.to_web(existing, config_format="instances")
    masked["instances"][1]["endpoint"] = "https://other.example.com/v1/chat/completions"
    with pytest.raises(ValidationError, match="重新输入"):
        AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)


def test_pool_new_name_does_not_restore_another_instances_secret():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    masked = AIBackendWebConfigAdapter.to_web(existing, config_format="instances")
    masked["instances"][0]["name"] = "new"
    updated = AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)
    renamed = next(item for item in updated["instances"] if item["name"] == "new")
    assert renamed["auth"]["header"]["Authorization"] != "Bearer alpha-secret"


def test_legacy_update_keeps_existing_instance_name():
    existing = AIBackendWebConfigAdapter.to_internal({"provider": "openai", "api_key": "secret"})
    existing["instances"][0]["name"] = "custom-name"
    masked = AIBackendWebConfigAdapter.to_web(existing)
    updated = AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)
    assert updated == existing
