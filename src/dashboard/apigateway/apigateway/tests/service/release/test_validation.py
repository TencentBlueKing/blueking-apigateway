#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
from django_dynamic_fixture import G
from rest_framework import serializers

from apigateway.core.constants import BackendKindEnum, GatewayStatusEnum, ResourceKindEnum
from apigateway.core.models import Backend, BackendConfig, ResourceVersion
from apigateway.service.release import PublishValidator, ReleaseValidationError, StageVarsValuesValidator

pytestmark = pytest.mark.django_db


def _standard_backend_config():
    return {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
    }


def _ai_backend_config():
    return {
        "timeout": 30000,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer must-not-leak"}},
                "options": {"model": "gpt-4.1-mini"},
            }
        ],
    }


def _create_backend_config(gateway, stage, *, name, kind, config):
    backend = G(Backend, gateway=gateway, name=name, kind=kind)
    backend_config = BackendConfig.objects.create(
        gateway=gateway,
        stage=stage,
        backend=backend,
        config=config,
    )
    return backend, backend_config


def _create_resource_version(gateway, backend, *, kind=ResourceKindEnum.STANDARD.value):
    resource = {
        "id": 1,
        "name": "chat-completions",
        "proxy": {"type": "http", "backend_id": backend.id, "config": "{}"},
        "plugins": [],
    }
    if kind is not None:
        resource["kind"] = kind

    resource_version = G(ResourceVersion, gateway=gateway)
    resource_version.data = [resource]
    resource_version.save(update_fields=["_data"])
    return resource_version


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


class TestPublishBackendKindValidation:
    @pytest.mark.parametrize("resource_kind", [ResourceKindEnum.STANDARD.value, None])
    def test_standard_backend_config_passes(self, fake_gateway, fake_stage, resource_kind):
        backend, _ = _create_backend_config(
            fake_gateway,
            fake_stage,
            name="standard-service",
            kind=BackendKindEnum.STANDARD.value,
            config=_standard_backend_config(),
        )
        resource_version = _create_resource_version(fake_gateway, backend, kind=resource_kind)

        assert PublishValidator(fake_gateway, fake_stage, resource_version)._validate_stage_backends() is None

    def test_ai_backend_config_passes_without_hosts(self, fake_gateway, fake_stage):
        backend, _ = _create_backend_config(
            fake_gateway,
            fake_stage,
            name="model-service",
            kind=BackendKindEnum.AI.value,
            config=_ai_backend_config(),
        )
        resource_version = _create_resource_version(fake_gateway, backend, kind=ResourceKindEnum.AI.value)

        assert PublishValidator(fake_gateway, fake_stage, resource_version)._validate_stage_backends() is None

    def test_invalid_ai_backend_config_does_not_expose_credentials(self, fake_gateway, fake_stage):
        invalid_config = _ai_backend_config()
        invalid_config["instances"][0]["options"] = {"model": ""}
        backend, _ = _create_backend_config(
            fake_gateway,
            fake_stage,
            name="model-service",
            kind=BackendKindEnum.AI.value,
            config=invalid_config,
        )
        resource_version = _create_resource_version(fake_gateway, backend, kind=ResourceKindEnum.AI.value)

        with pytest.raises(ReleaseValidationError) as exc_info:
            PublishValidator(fake_gateway, fake_stage, resource_version)._validate_stage_backends()

        message = str(exc_info.value)
        assert "model-service" in message
        assert "配置结构不合法" in message
        assert "Bearer must-not-leak" not in message

    def test_ai_backend_decryption_failure_is_sanitized(self, mocker, fake_gateway, fake_stage):
        backend, backend_config = _create_backend_config(
            fake_gateway,
            fake_stage,
            name="model-service",
            kind=BackendKindEnum.AI.value,
            config=_ai_backend_config(),
        )
        BackendConfig.objects.filter(pk=backend_config.pk).update(_config={"encrypted": "ciphertext-must-not-leak"})
        mocker.patch("apigateway.core.models.get_crypto").return_value.decrypt.side_effect = RuntimeError(
            "original-must-not-leak"
        )
        resource_version = _create_resource_version(fake_gateway, backend, kind=ResourceKindEnum.AI.value)

        with pytest.raises(ReleaseValidationError) as exc_info:
            PublishValidator(fake_gateway, fake_stage, resource_version)._validate_stage_backends()

        message = str(exc_info.value)
        assert "model-service" in message
        assert "ciphertext-must-not-leak" not in message
        assert "original-must-not-leak" not in message

    def test_resource_backend_kind_relationship_is_trusted(self, fake_gateway, fake_stage):
        backend, _ = _create_backend_config(
            fake_gateway,
            fake_stage,
            name="standard-service",
            kind=BackendKindEnum.STANDARD.value,
            config=_standard_backend_config(),
        )
        resource_version = _create_resource_version(fake_gateway, backend, kind=ResourceKindEnum.AI.value)

        assert PublishValidator(fake_gateway, fake_stage, resource_version)._validate_stage_backends() is None
