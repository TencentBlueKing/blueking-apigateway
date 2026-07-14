import copy

import pytest

from apigateway.core.backend_config_schema import (
    AI_BACKEND_CONFIG_SCHEMA,
    BackendConfigValidationError,
    validate_backend_config,
)
from apigateway.core.constants import AIBackendProviderEnum, BackendKindEnum


@pytest.fixture
def standard_backend_config():
    return {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "https", "host": "api.example.com", "weight": 100}],
    }


@pytest.fixture
def ai_backend_config():
    return {
        "timeout": 30000,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer secret"}},
                "options": {"model": "gpt-4o"},
            }
        ],
    }


def test_standard_schema_accepts_existing_config(standard_backend_config):
    validate_backend_config(BackendKindEnum.STANDARD.value, standard_backend_config)


def test_ai_schema_accepts_one_openai_instance(ai_backend_config):
    validate_backend_config(BackendKindEnum.AI.value, ai_backend_config)


def test_ai_schema_provider_enum_matches_shared_contract():
    provider_schema = AI_BACKEND_CONFIG_SCHEMA["properties"]["instances"]["items"]["properties"]["provider"]

    assert provider_schema["enum"] == AIBackendProviderEnum.get_values()


@pytest.mark.parametrize("patch", [{"instances": []}, {"unknown": True}, {"timeout": 0}])
def test_ai_schema_rejects_invalid_top_level(ai_backend_config, patch):
    with pytest.raises(BackendConfigValidationError):
        validate_backend_config(BackendKindEnum.AI.value, ai_backend_config | patch)


def test_ai_schema_reports_json_path(ai_backend_config):
    config = copy.deepcopy(ai_backend_config)
    config["instances"][0]["options"]["model"] = ""

    with pytest.raises(BackendConfigValidationError) as exc_info:
        validate_backend_config(BackendKindEnum.AI.value, config)

    assert exc_info.value.path == "$.instances[0].options.model"


def test_ai_schema_accepts_additional_json_options(ai_backend_config):
    ai_backend_config["instances"][0]["options"].update(
        {
            "temperature": 0.7,
            "stream": True,
            "metadata": {"tags": ["production", None]},
        }
    )

    validate_backend_config(BackendKindEnum.AI.value, ai_backend_config)


def test_validate_backend_config_rejects_unknown_kind(standard_backend_config):
    with pytest.raises(ValueError, match="unsupported backend kind"):
        validate_backend_config("unknown", standard_backend_config)
