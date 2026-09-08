#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import pytest
from django.core.management.base import CommandError

from apigateway.biz.sdk.exceptions import SDKConfigurationError
from apigateway.core.management.commands.validate_sdk_worker import Command


def test_validate_sdk_worker_skips_unrelated_django_system_checks():
    assert Command.requires_system_checks == []


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
