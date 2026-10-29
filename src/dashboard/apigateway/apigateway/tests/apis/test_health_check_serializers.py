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

import pytest

from apigateway.apis.v2.sync import serializers as sync_serializers
from apigateway.apis.web import serializers as web_serializers

pytestmark = pytest.mark.no_meta_schema


@pytest.fixture(params=[web_serializers, sync_serializers], ids=["web", "v2-sync"])
def serializers(request):
    return request.param


class TestActiveHealthySLZ:
    def test_valid_active_healthy(self, serializers):
        data = {"interval": 10, "successes": 2, "http_statuses": [200, 201]}
        slz = serializers.ActiveHealthySLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["interval"] == 10
        assert slz.validated_data["successes"] == 2
        assert slz.validated_data["http_statuses"] == [200, 201]

    def test_optional_fields(self, serializers):
        data = {}
        slz = serializers.ActiveHealthySLZ(data=data)
        assert slz.is_valid()

    def test_invalid_interval(self, serializers):
        data = {"interval": 0}
        slz = serializers.ActiveHealthySLZ(data=data)
        assert not slz.is_valid()

    def test_invalid_successes_range(self, serializers):
        data = {"successes": 300}
        slz = serializers.ActiveHealthySLZ(data=data)
        assert not slz.is_valid()


class TestPassiveHealthySLZ:
    def test_valid_passive_healthy(self, serializers):
        data = {"successes": 2, "http_statuses": [200]}
        slz = serializers.PassiveHealthySLZ(data=data)
        assert slz.is_valid()

    def test_no_interval_field(self, serializers):
        """Passive healthy should not have interval field"""
        data = {"successes": 2}
        slz = serializers.PassiveHealthySLZ(data=data)
        assert slz.is_valid()
        assert "interval" not in slz.validated_data


class TestActiveUnhealthySLZ:
    def test_valid_active_unhealthy(self, serializers):
        data = {
            "interval": 5,
            "http_failures": 3,
            "tcp_failures": 2,
            "timeouts": 1,
            "http_statuses": [500, 502, 503],
        }
        slz = serializers.ActiveUnhealthySLZ(data=data)
        assert slz.is_valid()

    def test_optional_fields(self, serializers):
        data = {"http_failures": 3}
        slz = serializers.ActiveUnhealthySLZ(data=data)
        assert slz.is_valid()


class TestPassiveUnhealthySLZ:
    def test_valid_passive_unhealthy(self, serializers):
        data = {"http_failures": 3, "http_statuses": [500]}
        slz = serializers.PassiveUnhealthySLZ(data=data)
        assert slz.is_valid()


class TestActiveCheckSLZ:
    def test_valid_active_check(self, serializers):
        data = {
            "type": "http",
            "timeout": 5,
            "http_path": "/health",
            "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
        }
        slz = serializers.ActiveCheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["type"] == "http"
        assert slz.validated_data["timeout"] == 5
        assert slz.validated_data["http_path"] == "/health"

    def test_default_type(self, serializers):
        data = {"http_path": "/health"}
        slz = serializers.ActiveCheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["type"] == "http"

    def test_with_unhealthy(self, serializers):
        data = {
            "type": "http",
            "unhealthy": {"interval": 5, "http_failures": 3, "http_statuses": [500, 502]},
        }
        slz = serializers.ActiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_with_both_healthy_and_unhealthy(self, serializers):
        data = {
            "type": "http",
            "http_path": "/health",
            "healthy": {"interval": 10, "successes": 2},
            "unhealthy": {"interval": 5, "http_failures": 3},
        }
        slz = serializers.ActiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_https_type(self, serializers):
        data = {"type": "https", "http_path": "/health", "https_verify_certificate": True}
        slz = serializers.ActiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_tcp_type(self, serializers):
        data = {"type": "tcp", "port": 8080}
        slz = serializers.ActiveCheckSLZ(data=data)
        assert slz.is_valid()


class TestPassiveCheckSLZ:
    def test_valid_passive_check(self, serializers):
        data = {"type": "http", "unhealthy": {"http_failures": 3, "http_statuses": [500, 502]}}
        slz = serializers.PassiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_default_type(self, serializers):
        data = {"unhealthy": {"http_failures": 3}}
        slz = serializers.PassiveCheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["type"] == "http"

    def test_with_healthy(self, serializers):
        data = {"type": "http", "healthy": {"successes": 2, "http_statuses": [200]}}
        slz = serializers.PassiveCheckSLZ(data=data)
        assert slz.is_valid()

    def test_with_both_healthy_and_unhealthy(self, serializers):
        data = {
            "type": "http",
            "healthy": {"successes": 2, "http_statuses": [200]},
            "unhealthy": {"http_failures": 3, "http_statuses": [500]},
        }
        slz = serializers.PassiveCheckSLZ(data=data)
        assert slz.is_valid()


class TestCheckSLZ:
    def test_active_only(self, serializers):
        data = {"active": {"type": "http", "http_path": "/health"}}
        slz = serializers.CheckSLZ(data=data)
        assert slz.is_valid()
        assert slz.validated_data["active"] is not None
        assert slz.validated_data.get("passive") is None

    def test_passive_only_invalid(self, serializers):
        data = {"passive": {"type": "http", "unhealthy": {"http_failures": 3}}}
        slz = serializers.CheckSLZ(data=data)
        assert not slz.is_valid()
        assert "active" in slz.errors

    def test_null_active_with_passive_invalid(self, serializers):
        data = {
            "active": None,
            "passive": {"type": "http", "unhealthy": {"http_failures": 3}},
        }
        slz = serializers.CheckSLZ(data=data)
        assert not slz.is_valid()
        assert "active" in slz.errors

    def test_neither_active_nor_passive(self, serializers):
        data = {}
        slz = serializers.CheckSLZ(data=data)
        assert not slz.is_valid()
        assert "active" in slz.errors

    def test_active_with_full_config(self, serializers):
        data = {
            "active": {
                "type": "http",
                "timeout": 5,
                "http_path": "/health",
                "concurrency": 10,
                "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
                "unhealthy": {"interval": 5, "http_failures": 3, "http_statuses": [500, 502, 503]},
            }
        }
        slz = serializers.CheckSLZ(data=data)
        assert slz.is_valid()

    def test_active_with_passive_full_config(self, serializers):
        data = {
            "active": {
                "type": "http",
                "timeout": 5,
                "http_path": "/health",
                "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
            },
            "passive": {
                "type": "http",
                "healthy": {"successes": 2, "http_statuses": [200]},
                "unhealthy": {"http_failures": 3, "tcp_failures": 2, "http_statuses": [500, 502]},
            },
        }
        slz = serializers.CheckSLZ(data=data)
        assert slz.is_valid()
