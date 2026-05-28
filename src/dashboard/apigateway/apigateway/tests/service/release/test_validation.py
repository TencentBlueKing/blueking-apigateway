#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from rest_framework import serializers

from apigateway.core.constants import GatewayStatusEnum
from apigateway.service.release import PublishValidator, ReleaseValidationError, StageVarsValuesValidator


def test_stage_vars_values_validator_uses_resource_version_stage_vars(mocker, fake_gateway):
    mocker.patch(
        "apigateway.service.release.validation.get_used_stage_vars",
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
        "apigateway.service.release.validation.get_used_stage_vars",
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
