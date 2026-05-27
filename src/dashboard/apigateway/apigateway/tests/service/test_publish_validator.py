import pytest
from rest_framework import serializers

from apigateway.core.constants import GatewayStatusEnum
from apigateway.service.publish_validator import PublishValidator, ReleaseValidationError, StageVarsValuesValidator


def test_stage_vars_values_validator_uses_resource_version_stage_vars(mocker, fake_gateway):
    mocker.patch(
        "apigateway.service.publish_validator.get_used_stage_vars",
        return_value={
            "in_path": ["prefix"],
            "in_host": ["domain"],
        },
    )

    validator = StageVarsValuesValidator()

    assert (
        validator(
            {
                "gateway": fake_gateway,
                "stage_name": "prod",
                "vars": {"prefix": "/api", "domain": "example.com"},
                "resource_version_id": 1,
            }
        )
        is None
    )


def test_stage_vars_values_validator_rejects_invalid_path_var(mocker, fake_gateway):
    mocker.patch(
        "apigateway.service.publish_validator.get_used_stage_vars",
        return_value={
            "in_path": ["prefix"],
            "in_host": [],
        },
    )

    validator = StageVarsValuesValidator()

    with pytest.raises(serializers.ValidationError):
        validator(
            {
                "gateway": fake_gateway,
                "stage_name": "prod",
                "vars": {"prefix": "/api?bad=true"},
                "resource_version_id": 1,
            }
        )


def test_publish_validator_rejects_inactive_gateway(fake_gateway, fake_stage, fake_resource_version):
    fake_gateway.status = GatewayStatusEnum.INACTIVE.value
    fake_gateway.save(update_fields=["status"])

    validator = PublishValidator(fake_gateway, fake_stage, fake_resource_version)

    with pytest.raises(ReleaseValidationError):
        validator._validate_gateway_status()
