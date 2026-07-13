import copy

import pytest

from apigateway.core.backend_config import (
    ENCRYPTED_SECRET_PREFIX,
    MASKED_SECRET,
    decrypt_ai_backend_config,
    mask_backend_config,
    prepare_backend_config,
)
from apigateway.core.backend_config_schema import BackendConfigValidationError
from apigateway.core.constants import BackendKindEnum


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


def test_prepare_encrypts_and_mask_hides_auth(ai_backend_config):
    stored = prepare_backend_config(BackendKindEnum.AI.value, ai_backend_config)

    assert stored["instances"][0]["auth"]["header"]["Authorization"].startswith(ENCRYPTED_SECRET_PREFIX)
    assert mask_backend_config(BackendKindEnum.AI.value, stored)["instances"][0]["auth"]["header"] == {
        "Authorization": MASKED_SECRET,
        "X-Organization": MASKED_SECRET,
    }
    assert decrypt_ai_backend_config(stored) == ai_backend_config


def test_prepare_masked_and_missing_header_keep_existing(ai_backend_config):
    existing = prepare_backend_config(BackendKindEnum.AI.value, ai_backend_config)
    masked = copy.deepcopy(ai_backend_config)
    masked["instances"][0]["auth"]["header"] = {"Authorization": MASKED_SECRET}
    missing = copy.deepcopy(ai_backend_config)
    del missing["instances"][0]["auth"]["header"]

    masked_result = prepare_backend_config(BackendKindEnum.AI.value, masked, existing)
    missing_result = prepare_backend_config(BackendKindEnum.AI.value, missing, existing)

    assert (
        masked_result["instances"][0]["auth"]["header"]["Authorization"]
        == existing["instances"][0]["auth"]["header"]["Authorization"]
    )
    assert missing_result["instances"][0]["auth"]["header"] == existing["instances"][0]["auth"]["header"]


def test_prepare_explicit_empty_header_clears_existing(ai_backend_config):
    existing = prepare_backend_config(BackendKindEnum.AI.value, ai_backend_config)
    incoming = copy.deepcopy(ai_backend_config)
    incoming["instances"][0]["auth"]["header"] = {}

    with pytest.raises(BackendConfigValidationError, match="Authorization header is required"):
        prepare_backend_config(BackendKindEnum.AI.value, incoming, existing)


def test_prepare_rejects_case_insensitive_duplicate_headers(ai_backend_config):
    ai_backend_config["instances"][0]["auth"]["header"]["authorization"] = "duplicate"

    with pytest.raises(BackendConfigValidationError, match="duplicate header"):
        prepare_backend_config(BackendKindEnum.AI.value, ai_backend_config)


@pytest.mark.parametrize(
    ("provider", "override", "error"),
    [
        ("openai", {"endpoint": "https://example.com/v1"}, "override is not allowed"),
        ("openai-compatible", None, "override.endpoint is required"),
    ],
)
def test_prepare_validates_provider_contract(ai_backend_config, provider, override, error):
    instance = ai_backend_config["instances"][0]
    instance["provider"] = provider
    if override is None:
        instance.pop("override", None)
    else:
        instance["override"] = override

    with pytest.raises(BackendConfigValidationError, match=error):
        prepare_backend_config(BackendKindEnum.AI.value, ai_backend_config)


def test_decrypt_rejects_plaintext_secret(ai_backend_config):
    with pytest.raises(BackendConfigValidationError, match="encrypted envelope"):
        decrypt_ai_backend_config(ai_backend_config)


def test_standard_config_is_validated_without_secret_processing():
    config = {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com"}],
    }

    assert prepare_backend_config(BackendKindEnum.STANDARD.value, config) == config
    assert mask_backend_config(BackendKindEnum.STANDARD.value, config) == config
