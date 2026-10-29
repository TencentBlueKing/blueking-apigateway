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

from apigateway.apis.v2.sync.serializers import BackendConfigSLZ


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

    def test_backend_config_with_passive_only_checks_invalid(self):
        """Test backend config rejects passive-only health checks"""
        data = {
            "loadbalance": "roundrobin",
            "timeout": 30,
            "hosts": [{"host": "http://example.com", "weight": 100}],
            "checks": {"passive": {"type": "http", "unhealthy": {"http_failures": 3}}},
        }
        slz = BackendConfigSLZ(data=data)
        assert not slz.is_valid()
        assert "active" in slz.errors["checks"]

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
