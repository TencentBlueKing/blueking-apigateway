# -*- coding: utf-8 -*-
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

from apigateway.apps.data_plane.constants import DataPlaneApisixVersionEnum
from apigateway.controller.convertor.service import ServiceConvertor
from apigateway.controller.models import ActiveCheck, Check, PassiveCheck
from apigateway.controller.release_data import StageBackendConfig
from apigateway.core.constants import BackendKindEnum

APISIX_VERSION_3_13 = DataPlaneApisixVersionEnum.V3_13.value


def _set_standard_backend_configs(release_data, backend, backend_configs):
    release_data.stage_backend_configs = {
        backend_id: StageBackendConfig(
            backend_id=backend_id,
            backend_name=backend.name,
            backend_kind=BackendKindEnum.STANDARD.value,
            backend_type=backend.type,
            config=config,
        )
        for backend_id, config in backend_configs.items()
    }


class TestHealthCheckConversion:
    def test_convert_active_check(self, fake_release_data, fake_backend):
        """Test converting active health check from backend_config to BaseUpstream"""
        backend_configs = {
            fake_backend.id: {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                "checks": {
                    "active": {
                        "type": "http",
                        "timeout": 5,
                        "http_path": "/health",
                        "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
                        "unhealthy": {"interval": 5, "http_failures": 3, "http_statuses": [500, 502, 503]},
                    }
                },
            }
        }

        _set_standard_backend_configs(fake_release_data, fake_backend, backend_configs)

        convertor = ServiceConvertor(
            release_data=fake_release_data,
            publish_id=1,
            apisix_version=APISIX_VERSION_3_13,
        )
        services = convertor.convert()

        assert len(services) == 1
        service = services[0]

        # Verify checks field is set
        assert service.upstream.checks is not None
        assert isinstance(service.upstream.checks, Check)

        # Verify active check
        assert service.upstream.checks.active is not None
        assert isinstance(service.upstream.checks.active, ActiveCheck)
        assert service.upstream.checks.active.http_path == "/health"
        assert service.upstream.checks.active.timeout == 5

        # Verify healthy config
        assert service.upstream.checks.active.healthy is not None
        assert service.upstream.checks.active.healthy.interval == 10
        assert service.upstream.checks.active.healthy.successes == 2
        assert service.upstream.checks.active.healthy.http_statuses == [200, 201]

        # Verify unhealthy config
        assert service.upstream.checks.active.unhealthy is not None
        assert service.upstream.checks.active.unhealthy.interval == 5
        assert service.upstream.checks.active.unhealthy.http_failures == 3
        assert service.upstream.checks.active.unhealthy.http_statuses == [500, 502, 503]

        # Verify passive check is None
        assert service.upstream.checks.passive is None

    def test_convert_passive_check(self, fake_release_data, fake_backend):
        """Test converting passive health check from backend_config to BaseUpstream"""
        backend_configs = {
            fake_backend.id: {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                "checks": {
                    "passive": {
                        "type": "http",
                        "healthy": {"successes": 2, "http_statuses": [200]},
                        "unhealthy": {"http_failures": 3, "tcp_failures": 2, "http_statuses": [500, 502]},
                    }
                },
            }
        }

        _set_standard_backend_configs(fake_release_data, fake_backend, backend_configs)

        convertor = ServiceConvertor(
            release_data=fake_release_data,
            publish_id=1,
            apisix_version=APISIX_VERSION_3_13,
        )
        services = convertor.convert()

        assert len(services) == 1
        service = services[0]

        # Verify checks field is set
        assert service.upstream.checks is not None
        assert isinstance(service.upstream.checks, Check)

        # Verify passive check
        assert service.upstream.checks.passive is not None
        assert isinstance(service.upstream.checks.passive, PassiveCheck)

        # Verify healthy config
        assert service.upstream.checks.passive.healthy is not None
        assert service.upstream.checks.passive.healthy.successes == 2
        assert service.upstream.checks.passive.healthy.http_statuses == [200]

        # Verify unhealthy config
        assert service.upstream.checks.passive.unhealthy is not None
        assert service.upstream.checks.passive.unhealthy.http_failures == 3
        assert service.upstream.checks.passive.unhealthy.tcp_failures == 2
        assert service.upstream.checks.passive.unhealthy.http_statuses == [500, 502]

        # Verify active check is None
        assert service.upstream.checks.active is None

    def test_convert_without_checks(self, fake_release_data, fake_backend):
        """Test that absence of checks results in None upstream.checks"""
        backend_configs = {
            fake_backend.id: {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
            }
        }

        _set_standard_backend_configs(fake_release_data, fake_backend, backend_configs)

        convertor = ServiceConvertor(
            release_data=fake_release_data,
            publish_id=1,
            apisix_version=APISIX_VERSION_3_13,
        )
        services = convertor.convert()

        assert len(services) == 1
        service = services[0]

        # Verify checks field is None when not configured
        assert service.upstream.checks is None

    def test_convert_active_check_with_minimal_config(self, fake_release_data, fake_backend):
        """Test converting active check with only required fields"""
        backend_configs = {
            fake_backend.id: {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                "checks": {"active": {"type": "http", "http_path": "/health"}},
            }
        }

        _set_standard_backend_configs(fake_release_data, fake_backend, backend_configs)

        convertor = ServiceConvertor(
            release_data=fake_release_data,
            publish_id=1,
            apisix_version=APISIX_VERSION_3_13,
        )
        services = convertor.convert()

        assert len(services) == 1
        service = services[0]

        assert service.upstream.checks is not None
        assert service.upstream.checks.active is not None
        assert service.upstream.checks.active.http_path == "/health"
        assert service.upstream.checks.active.type.value == "http"

    def test_convert_tcp_active_check(self, fake_release_data, fake_backend):
        """Test converting TCP active health check"""
        backend_configs = {
            fake_backend.id: {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                "checks": {
                    "active": {
                        "type": "tcp",
                        "timeout": 3,
                        "unhealthy": {"tcp_failures": 2},
                    }
                },
            }
        }

        _set_standard_backend_configs(fake_release_data, fake_backend, backend_configs)

        convertor = ServiceConvertor(
            release_data=fake_release_data,
            publish_id=1,
            apisix_version=APISIX_VERSION_3_13,
        )
        services = convertor.convert()

        assert len(services) == 1
        service = services[0]

        assert service.upstream.checks.active.type.value == "tcp"
        assert service.upstream.checks.active.unhealthy.tcp_failures == 2

    def test_serialization_excludes_none(self, fake_release_data, fake_backend):
        """Test that None values are excluded from serialization"""
        backend_configs = {
            fake_backend.id: {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                "checks": {"active": {"type": "http", "http_path": "/health"}},
            }
        }

        _set_standard_backend_configs(fake_release_data, fake_backend, backend_configs)

        convertor = ServiceConvertor(
            release_data=fake_release_data,
            publish_id=1,
            apisix_version=APISIX_VERSION_3_13,
        )
        services = convertor.convert()

        service = services[0]

        # Serialize to dict and verify None fields are excluded
        service_dict = service.model_dump(exclude_none=True)

        # Checks should be present
        assert "checks" in service_dict["upstream"]

        # Active should be present
        assert "active" in service_dict["upstream"]["checks"]

        # Passive should be excluded (it's None)
        assert "passive" not in service_dict["upstream"]["checks"]

        # Optional fields with None should be excluded
        active_check = service_dict["upstream"]["checks"]["active"]
        assert "http_path" in active_check
        assert "timeout" not in active_check  # Was None, should be excluded
