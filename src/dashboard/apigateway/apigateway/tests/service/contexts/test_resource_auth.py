import pytest

from apigateway.service.contexts import with_resource_auth_derived_fields


@pytest.mark.parametrize(
    "config, expected_auth_type, expected_delegated",
    [
        ({"auth_verified_required": True, "app_verified_required": True}, "user", True),
        ({"auth_verified_required": True, "app_verified_required": False}, "user", False),
        ({"auth_verified_required": False, "app_verified_required": True}, "app", False),
        ({"auth_verified_required": False, "app_verified_required": False}, "none", False),
    ],
)
def test_with_resource_auth_derived_fields(config, expected_auth_type, expected_delegated):
    config = {**config, "resource_perm_required": False, "oauth2_public_client_enabled": False}

    result = with_resource_auth_derived_fields(config)

    assert result == {
        **config,
        "auth_type": expected_auth_type,
        "oauth2_app_delegated_enabled": expected_delegated,
    }
    assert "auth_type" not in config
