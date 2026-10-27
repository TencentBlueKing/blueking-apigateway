from copy import deepcopy

import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.ai_backend import AIBackendWebConfigAdapter, AIBackendWebConfigNotRepresentable
from apigateway.common.error_codes import APIError


def _single_form(**fields):
    return {
        "timeout": 300,
        "instances": [{"name": "primary", "priority": 10, "provider": "openai", "api_key": "secret", **fields}],
    }


def _pool_form():
    return {
        "timeout": 60,
        "balancer": {"algorithm": "chash"},
        "instances": [
            {"name": "a", "priority": 10, "provider": "openai", "api_key": "alpha-secret"},
            {
                "name": "b",
                "priority": 0,
                "provider": "openai-compatible",
                "endpoint": "https://backup.example.com/v1/chat/completions",
                "auth_header": {"name": "X-Key", "value": "beta-secret"},
            },
        ],
    }


def test_adapter_maps_builtin_instance_to_storage_and_back():
    stored = AIBackendWebConfigAdapter.to_internal(_single_form())
    assert stored == {
        "timeout": 300,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "priority": 10,
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer secret"}},
                "options": {},
            }
        ],
    }
    assert AIBackendWebConfigAdapter.to_web(stored) == {
        "timeout": 300,
        "instances": [
            {
                "name": "primary",
                "priority": 10,
                "provider": "openai",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "model_endpoint": "https://api.openai.com/v1/models",
                "api_key": "se****et",
                "auth_header": None,
                "model": None,
                "model_options": {},
            }
        ],
    }


def test_adapter_maps_optional_custom_instance_to_storage_and_back():
    stored = AIBackendWebConfigAdapter.to_internal(
        {
            "instances": [
                {
                    "name": "primary",
                    "priority": 10,
                    "provider": "openai-compatible",
                    "endpoint": "https://llm.example.com/v1/chat/completions",
                }
            ]
        }
    )
    assert stored["instances"] == [
        {
            "name": "primary",
            "priority": 10,
            "provider": "openai-compatible",
            "weight": 1,
            "options": {},
            "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
        }
    ]
    instance = AIBackendWebConfigAdapter.to_web(stored)["instances"][0]
    assert instance["auth_header"] is None and instance["model_endpoint"] is None


def test_adapter_preserves_exact_mask_only_for_same_destination():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    masked = AIBackendWebConfigAdapter.to_web(existing)
    assert masked["balancer"] == {"algorithm": "chash"}
    assert masked["instances"][0]["api_key"] == "al****et"
    masked["instances"].reverse()
    assert AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing) == existing


@pytest.mark.parametrize("change", ["destination", "header"])
def test_adapter_rejects_masked_credential_after_identity_change(change):
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    masked = AIBackendWebConfigAdapter.to_web(existing)
    instance = masked["instances"][1]
    if change == "destination":
        instance["endpoint"] = "https://other.example.com/v1/chat/completions"
    else:
        instance["auth_header"]["name"] = "X-Other-Key"
    with pytest.raises(ValidationError, match="重新输入"):
        AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)


def test_adapter_fails_closed_when_storage_has_multiple_headers():
    config = {
        "instances": [
            {
                "name": "primary",
                "provider": "openai-compatible",
                "auth": {"header": {"X-Api-Key": "secret", "X-Tenant": "tenant"}},
                "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
            }
        ]
    }
    with pytest.raises(AIBackendWebConfigNotRepresentable, match="multiple auth headers"):
        AIBackendWebConfigAdapter.to_web(config)


@pytest.mark.parametrize("index, field", [(0, "api_key"), (1, "auth_header")])
@pytest.mark.parametrize("change", ["rename", "new_config", "replace_mask"])
@pytest.mark.parametrize("operation", ["save", "probe"])
def test_unrestorable_mask_is_rejected(index, field, change, operation):
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    masked = AIBackendWebConfigAdapter.to_web(existing)
    instance = masked["instances"][index]
    if change == "rename":
        instance["name"] = "new"
    elif change == "new_config":
        existing = None
        masked["instances"][1 - index] = _pool_form()["instances"][1 - index]
    elif field == "api_key":
        instance[field] = "xy****zz"
    else:
        instance[field]["value"] = "xy****zz"
    with pytest.raises(ValidationError, match="重新输入") as err:
        if operation == "save":
            AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)
        else:
            AIBackendWebConfigAdapter.to_connectivity(instance, existing_config=existing)
    assert field in err.value.detail


@pytest.mark.parametrize("credential", ["****", "ab****cd", "********"])
def test_new_instance_rejects_mask_placeholders(credential):
    with pytest.raises(ValidationError, match="重新输入"):
        AIBackendWebConfigAdapter.to_internal(_single_form(api_key=credential))


@pytest.mark.parametrize("credential", ["key*with*stars", "abc****xyz", "***", "a***b"])
def test_new_instance_accepts_literal_credentials_with_stars(credential):
    stored = AIBackendWebConfigAdapter.to_internal(_single_form(api_key=credential))
    assert stored["instances"][0]["auth"]["header"]["Authorization"] == f"Bearer {credential}"


def test_renamed_instance_accepts_reentered_credential():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    form = AIBackendWebConfigAdapter.to_web(existing)
    form["instances"][0].update(name="new", api_key="replacement-secret")
    updated = AIBackendWebConfigAdapter.to_internal(form, existing_config=existing)
    renamed = next(item for item in updated["instances"] if item["name"] == "new")
    assert renamed["auth"]["header"]["Authorization"] == "Bearer replacement-secret"


def test_historical_single_instance_is_read_as_array_without_modifying_storage():
    existing = {
        "timeout": 300,
        "instances": [
            {
                "name": "custom-name",
                "provider": "openai",
                "weight": 0,
                "auth": {"header": {"Authorization": "Bearer secret"}},
            }
        ],
    }
    before = deepcopy(existing)
    masked = AIBackendWebConfigAdapter.to_web(existing)
    assert masked["instances"][0]["name"] == "custom-name"
    assert masked["instances"][0]["priority"] == 10
    assert "fallback_strategy" not in masked
    assert existing == before
    updated = AIBackendWebConfigAdapter.to_internal(masked, existing_config=existing)
    assert updated["instances"][0]["auth"] == existing["instances"][0]["auth"]


def test_connectivity_can_probe_backup_independently_and_restore_its_own_credentials():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    backup = AIBackendWebConfigAdapter.to_web(existing)["instances"][1]
    probe = AIBackendWebConfigAdapter.to_connectivity(backup, existing_config=existing)
    assert probe["name"] == "b"
    assert probe["auth"]["header"] == {"X-Key": "beta-secret"}
    assert not {"instances", "timeout", "weight", "balancer", "fallback_strategy"} & probe.keys()


@pytest.mark.parametrize(
    "patch",
    [
        {"balancer": {"algorithm": "chash", "hash_on": "header", "key": "X-App"}},
        {"fallback_strategy": ["rate_limiting"]},
    ],
)
def test_web_rejects_unrepresentable_routing_without_modifying_storage(patch):
    config = AIBackendWebConfigAdapter.to_internal(_pool_form())
    config.update(patch)
    before = deepcopy(config)
    with pytest.raises(AIBackendWebConfigNotRepresentable):
        AIBackendWebConfigAdapter.to_web(config)
    assert config == before


def test_update_checks_submitted_names_instead_of_rejecting_existing_duplicates():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    existing["instances"].append(deepcopy(existing["instances"][0]))
    updated = AIBackendWebConfigAdapter.to_internal(_single_form(), existing_config=existing)
    assert [instance["name"] for instance in updated["instances"]] == ["primary"]
    assert updated["instances"][0]["auth"]["header"]["Authorization"] == "Bearer secret"


@pytest.mark.parametrize("algorithm", ["roundrobin", "chash"])
def test_pool_reduced_to_single_primary_discards_routing_and_preserves_credentials(algorithm):
    form = _pool_form()
    form["balancer"] = {"algorithm": algorithm}
    existing = AIBackendWebConfigAdapter.to_internal(form)
    form = AIBackendWebConfigAdapter.to_web(existing)
    form["instances"] = [form["instances"][0]]
    before = deepcopy(form)

    updated = AIBackendWebConfigAdapter.to_internal(form, existing_config=existing)

    assert len(updated["instances"]) == 1
    assert updated["instances"][0]["auth"]["header"]["Authorization"] == "Bearer alpha-secret"
    assert updated["timeout"] == 60
    assert "balancer" not in updated and "fallback_strategy" not in updated
    assert form == before


def test_pool_reduced_to_only_backup_still_requires_a_primary():
    existing = AIBackendWebConfigAdapter.to_internal(_pool_form())
    form = AIBackendWebConfigAdapter.to_web(existing)
    form["instances"] = [form["instances"][1]]
    with pytest.raises(APIError, match="至少需要一个主实例"):
        AIBackendWebConfigAdapter.to_internal(form, existing_config=existing)


@pytest.mark.parametrize("invalid, field", [("header", "auth"), ("stage_var", "non_field_errors")])
def test_probe_reports_new_instance_validation_like_save(invalid, field):
    instance = {
        "name": "pending",
        "priority": 10,
        "provider": "openai-compatible",
        "endpoint": "https://llm.example.com/v1/chat/completions",
        "auth_header": {"name": "X-Key", "value": "probe-key"},
        "model_options": {},
    }
    if invalid == "header":
        instance["auth_header"]["name"] = "Host"
    else:
        instance["model_options"] = {"region": "{env.region}"}
    with pytest.raises(ValidationError) as saved:
        AIBackendWebConfigAdapter.to_internal({"instances": [instance]})
    with pytest.raises(ValidationError) as probed:
        AIBackendWebConfigAdapter.to_connectivity(instance)
    assert probed.value.detail == {field: saved.value.detail["instances"]}
    assert "已有" not in str(probed.value.detail)


def test_probe_keeps_existing_configuration_parse_error_separate():
    with pytest.raises(ValidationError, match="已有模型服务配置无法通过 Web 接口编辑"):
        AIBackendWebConfigAdapter.to_connectivity(_single_form()["instances"][0], existing_config={"instances": []})
