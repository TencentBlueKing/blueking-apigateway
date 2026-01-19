# -*- coding: utf-8 -*-
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

from apigateway.apis.v2.sync.serializers import (
    ActiveCheckSLZ,
    ActiveHealthySLZ,
    ActiveUnhealthySLZ,
    BackendConfigSLZ,
    CheckSLZ,
    PassiveCheckSLZ,
    PassiveHealthySLZ,
    PassiveUnhealthySLZ,
)


class TestActiveHealthySLZ:
    def test_valid_active_healthy(self):
        data = {"interval": 10, "successes": 2, "http_statuses": [200, 201]}
        slz = ActiveHealthySLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["interval"] == 10
        assert slz.validated_data["successes"] == 2
        assert slz.validated_data["http_statuses"] == [200, 201]

    def test_optional_fields(self):
        data = {}
        slz = ActiveHealthySLZ(data=data)
        assert slz.is_valid()

    def test_invalid_interval(self):
        data = {"interval": 0}
        slz = ActiveHealthySLZ(data=data)
        assert not slz.is_valid()

    def test_invalid_successes_range(self):
        data = {"successes": 300}
        slz = ActiveHealthySLZ(data=data)
        assert not slz.is_valid()


class TestPassiveHealthySLZ:
    def test_valid_passive_healthy(self):
        data = {"successes": 2, "http_statuses": [200]}
        slz = PassiveHealthySLZ(data=data)
        assert slz.is_valid()

    def test_no_interval_field(self):
        """Passive healthy should not have interval field"""
        data = {"successes": 2}
        slz = PassiveHealthySLZ(data=data)
        assert slz.is_valid()
        assert "interval" not in slz.validated_data


class TestActiveUnhealthySLZ:
    def test_valid_active_unhealthy(self):
        data = {
            "interval": 5,
            "http_failures": 3,
            "tcp_failures": 2,
            "timeouts": 1,
            "http_statuses": [500, 502, 503],
        }
        slz = ActiveUnhealthySLZ(data=data)
        assert slz.is_valid()

    def test_optional_fields(self):
        data = {"http_failures": 3}
        slz = ActiveUnhealthySLZ(data=data)
        assert slz.is_valid()


class TestPassiveUnhealthySLZ:
    def test_valid_passive_unhealthy(self):
        data = {"http_failures": 3, "http_statuses": [500]}
        slz = PassiveUnhealthySLZ(data=data)
        assert slz.is_valid()


class TestActiveCheckSLZ:
    def test_valid_active_check(self):
        data = {
            "type": "http",
            "timeout": 5,
            "http_path": "/health",
            "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
        }
        slz = ActiveCheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["type"] == "http"
        assert slz.validated_data["timeout"] == 5
        assert slz.validated_data["http_path"] == "/health"

    def test_default_type(self):
        data = {"http_path": "/health"}
        slz = ActiveCheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["type"] == "http"

    def test_with_unhealthy(self):
        data = {
            "type": "http",
            "unhealthy": {"interval": 5, "http_failures": 3, "http_statuses": [500, 502]},
        }
        slz = ActiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_with_both_healthy_and_unhealthy(self):
        data = {
            "type": "http",
            "http_path": "/health",
            "healthy": {"interval": 10, "successes": 2},
            "unhealthy": {"interval": 5, "http_failures": 3},
        }
        slz = ActiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_https_type(self):
        data = {"type": "https", "http_path": "/health", "https_verify_certificate": True}
        slz = ActiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_tcp_type(self):
        data = {"type": "tcp", "port": 8080}
        slz = ActiveCheckSLZ(data=data)
        assert slz.is_valid()


class TestPassiveCheckSLZ:
    def test_valid_passive_check(self):
        data = {"type": "http", "unhealthy": {"http_failures": 3, "http_statuses": [500, 502]}}
        slz = PassiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_default_type(self):
        data = {"unhealthy": {"http_failures": 3}}
        slz = PassiveCheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["type"] == "http"

    def test_with_healthy(self):
        data = {"type": "http", "healthy": {"successes": 2, "http_statuses": [200]}}
        slz = PassiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_with_both_healthy_and_unhealthy(self):
        data = {
            "type": "http",
            "healthy": {"successes": 2, "http_statuses": [200]},
            "unhealthy": {"http_failures": 3, "http_statuses": [500]},
        }
        slz = PassiveCheckSLZ(data=data)
        assert slz.is_valid()


class TestCheckSLZ:
    def test_active_only(self):
        data = {"active": {"type": "http", "http_path": "/health"}}
        slz = CheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["active"] is not None
        assert slz.validated_data.get("passive") is None

    def test_passive_only(self):
        data = {"passive": {"type": "http", "unhealthy": {"http_failures": 3}}}
        slz = CheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["passive"] is not None
        assert slz.validated_data.get("active") is None

    def test_neither_active_nor_passive(self):
        data = {}
        slz = CheckSLZ(data=data)
        assert not slz.is_valid()
        assert "至少需要配置" in str(slz.errors)

    def test_active_with_full_config(self):
        data = {
            "active": {
                "type": "http",
                "timeout": 5,
                "http_path": "/health",
                "host": "example.com",
                "port": 8080,
                "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
                "unhealthy": {"interval": 5, "http_failures": 3, "http_statuses": [500, 502, 503]},
            }
        }
        slz = CheckSLZ(data=data)
        assert slz.is_valid()

    def test_passive_with_full_config(self):
        data = {
            "passive": {
                "type": "http",
                "healthy": {"successes": 2, "http_statuses": [200]},
                "unhealthy": {"http_failures": 3, "tcp_failures": 2, "http_statuses": [500, 502]},
            }
        }
        slz = CheckSLZ(data=data)
        assert slz.is_valid()


class TestBackendConfigSLZ:
    def test_backend_config_without_checks(self):
        """Test backend config without health checks (backward compatibility)"""
        data = {
            "loadbalance": "roundrobin",
            "timeout": 30,
            "hosts": [{"host": "http://example.com", "weight": 100}],
        }
        slz = BackendConfigSLZ(data=data)
        assert slz.is_valid()
        assert "checks" not in slz.validated_data or slz.validated_data.get("checks") is None

    def test_backend_config_with_active_checks(self):
        """Test backend config with active health checks"""
        data = {
            "loadbalance": "roundrobin",
            "timeout": 30,
            "hosts": [{"host": "http://example.com", "weight": 100}],
            "checks": {
                "active": {
                    "type": "http",
                    "http_path": "/health",
                    "healthy": {"interval": 10, "successes": 2},
                }
            },
        }
        slz = BackendConfigSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["checks"] is not None
        assert slz.validated_data["checks"]["active"] is not None

    def test_backend_config_with_passive_checks(self):
        """Test backend config with passive health checks"""
        data = {
            "loadbalance": "roundrobin",
            "timeout": 30,
            "hosts": [{"host": "http://example.com", "weight": 100}],
            "checks": {"passive": {"type": "http", "unhealthy": {"http_failures": 3}}},
        }
        slz = BackendConfigSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["checks"] is not None
        assert slz.validated_data["checks"]["passive"] is not None

    def test_backend_config_with_null_checks(self):
        """Test backend config with null checks field"""
        data = {
            "loadbalance": "roundrobin",
            "timeout": 30,
            "hosts": [{"host": "http://example.com", "weight": 100}],
            "checks": None,
        }
        slz = BackendConfigSLZ(data=data)
        assert slz.is_valid()
