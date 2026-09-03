import pytest
from django.core.management.base import CommandError

from apigateway.biz.sdk.exceptions import SDKConfigurationError
from apigateway.core.management.commands.validate_sdk_worker import Command


def test_validate_sdk_worker_reports_validated_identity(mocker):
    validate = mocker.patch(
        "apigateway.core.management.commands.validate_sdk_worker.validate_sdk_worker_environment",
        return_value={"openapi_generator": "7.23.0", "go": "1.24.4"},
    )
    command = Command()
    command.stdout = mocker.Mock()

    command.handle()

    validate.assert_called_once_with()
    command.stdout.write.assert_called_once()


def test_validate_sdk_worker_wraps_configuration_errors(mocker):
    mocker.patch(
        "apigateway.core.management.commands.validate_sdk_worker.validate_sdk_worker_environment",
        side_effect=SDKConfigurationError("missing npm"),
    )

    with pytest.raises(CommandError, match="missing npm"):
        Command().handle()
