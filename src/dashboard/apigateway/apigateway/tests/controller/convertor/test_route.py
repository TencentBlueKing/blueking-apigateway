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

import json

import pytest

from apigateway.controller.convertor import RouteConvertor
from apigateway.controller.convertor.constants import MATCH_SUB_PATH_PRIORITY, SUBPATH_PARAM_NAME
from apigateway.controller.models import Route, Timeout
from apigateway.controller.models.constants import HttpMethodEnum
from apigateway.core.constants import ProxyTypeEnum


class TestRouteConvertor:
    """Test RouteConvertor class"""

    @pytest.fixture
    def mock_release_data(self, mocker):
        """Mock release data"""
        mock_data = mocker.Mock()
        mock_data.gateway.name = "test-gateway"
        mock_data.stage.name = "test-stage"
        mock_data.stage.vars = {"env": "test"}
        mock_data.resource_version.data = []
        mock_data.get_resource_plugins.return_value = []
        return mock_data

    @pytest.fixture
    def backend_service_mapping(self):
        """Backend service mapping"""
        return {1: "test-service-id", 2: "another-service-id"}

    @pytest.fixture
    def convertor(self, mock_release_data, backend_service_mapping):
        """Create RouteConvertor instance"""
        return RouteConvertor(
            release_data=mock_release_data,
            backend_service_mapping=backend_service_mapping,
            publish_id=123,
            revoke_flag=False,
        )

    def test_init(self, mock_release_data, backend_service_mapping):
        """Test RouteConvertor initialization"""
        convertor = RouteConvertor(
            release_data=mock_release_data,
            backend_service_mapping=backend_service_mapping,
            publish_id=123,
            revoke_flag=True,
        )
        assert convertor._publish_id == 123
        assert convertor._revoke_flag is True
        assert convertor._backend_service_mapping == backend_service_mapping

    def test_get_service_id(self, convertor):
        """Test _get_service_id method"""
        # Test existing backend_id
        service_id = convertor._get_service_id(1)
        assert service_id == "test-service-id"

        # Test another backend_id
        service_id = convertor._get_service_id(2)
        assert service_id == "another-service-id"

        # Test non-existent backend_id
        with pytest.raises(NameError, match="stage service not found in registry"):
            convertor._get_service_id(999)

    def test_convert_with_revoke_flag(self, mock_release_data, backend_service_mapping):
        """Test convert method with revoke flag"""
        convertor = RouteConvertor(
            release_data=mock_release_data,
            backend_service_mapping=backend_service_mapping,
            publish_id=None,
            revoke_flag=True,
        )
        routes = convertor.convert()
        assert routes == []

    def test_convert_with_publish_id(self, mock_release_data, backend_service_mapping):
        """Test convert method with publish_id"""
        convertor = RouteConvertor(
            release_data=mock_release_data,
            backend_service_mapping=backend_service_mapping,
            publish_id=123,
            revoke_flag=False,
        )
        routes = convertor.convert()
        # Should have the release version detect route
        assert len(routes) == 1
        route = routes[0]
        assert isinstance(route, Route)
        assert route.id == "test-gateway.test-stage.-1"
        assert "builtin-mock-release-version" in route.name
        assert route.uris == ["/api/test-gateway/test-stage/__apigw_version"]
        assert route.methods == [HttpMethodEnum.GET]

    def test_convert_http_route(self, convertor, mock_release_data):
        """Test _convert_http_route method"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "description": "test description",
            "method": "GET",
            "path": "/test/path",
            "disabled_stages": [],
            "enable_websocket": False,
            "proxy": {
                "type": ProxyTypeEnum.HTTP.value,
                "backend_id": 1,
                "config": json.dumps(
                    {
                        "method": "GET",
                        "path": "/backend/path",
                        "timeout": 30,
                        "match_subpath": False,
                    }
                ),
            },
            "contexts": {
                "resource_auth": {
                    "config": json.dumps(
                        {
                            "app_verified_required": True,
                            "auth_verified_required": True,
                            "resource_perm_required": True,
                            "skip_auth_verification": False,
                        }
                    )
                }
            },
        }

        route = convertor._convert_http_route(resource)
        assert route is not None
        assert isinstance(route, Route)
        assert route.id == "test-gateway.test-stage.1"
        assert route.service_id == "test-service-id"
        assert route.methods == [HttpMethodEnum.GET]
        assert len(route.plugins) > 0
        assert "bk-resource-context" in route.plugins
        assert "bk-proxy-rewrite" in route.plugins

    def test_convert_http_route_with_any_method(self, convertor, mock_release_data):
        """Test _convert_http_route with ANY method"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "method": "ANY",
            "path": "/test/path",
            "disabled_stages": [],
            "proxy": {
                "type": ProxyTypeEnum.HTTP.value,
                "backend_id": 1,
                "config": json.dumps({"method": "ANY", "path": "/backend/path"}),
            },
            "contexts": {"resource_auth": {"config": json.dumps({})}},
        }

        route = convertor._convert_http_route(resource)
        assert route is not None
        assert route.methods == []

    def test_convert_http_route_disabled_stage(self, convertor, mock_release_data):
        """Test _convert_http_route with disabled stage"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "method": "GET",
            "path": "/test/path",
            "disabled_stages": ["test-stage"],
            "proxy": {
                "type": ProxyTypeEnum.HTTP.value,
                "backend_id": 1,
                "config": json.dumps({}),
            },
            "contexts": {"resource_auth": {"config": json.dumps({})}},
        }

        route = convertor._convert_http_route(resource)
        assert route is None

    def test_convert_http_route_non_http_proxy(self, convertor, mock_release_data):
        """Test _convert_http_route with non-HTTP proxy type"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "method": "GET",
            "path": "/test/path",
            "disabled_stages": [],
            "proxy": {
                "type": "MOCK",
                "backend_id": 1,
                "config": json.dumps({}),
            },
            "contexts": {"resource_auth": {"config": json.dumps({})}},
        }

        route = convertor._convert_http_route(resource)
        assert route is None

    def test_convert_http_route_missing_backend_id(self, convertor, mock_release_data):
        """Test _convert_http_route with missing backend_id"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "method": "GET",
            "path": "/test/path",
            "disabled_stages": [],
            "proxy": {
                "type": ProxyTypeEnum.HTTP.value,
                "backend_id": 0,
                "config": json.dumps({}),
            },
            "contexts": {"resource_auth": {"config": json.dumps({})}},
        }

        with pytest.raises(ValueError, match="backend_id is 0 or not set"):
            convertor._convert_http_route(resource)

    def test_convert_http_route_with_websocket(self, convertor, mock_release_data):
        """Test _convert_http_route with websocket enabled"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "method": "GET",
            "path": "/test/path",
            "disabled_stages": [],
            "enable_websocket": True,
            "proxy": {
                "type": ProxyTypeEnum.HTTP.value,
                "backend_id": 1,
                "config": json.dumps({}),
            },
            "contexts": {"resource_auth": {"config": json.dumps({})}},
        }

        route = convertor._convert_http_route(resource)
        assert route.enable_websocket is True

    def test_convert_uris_simple(self, convertor, mock_release_data):
        """Test _convert_uris with simple path"""
        uris, priority = convertor._convert_uris("/test/path", match_subpath=False)
        assert len(uris) == 2
        assert "/api/test-gateway/test-stage/test/path" in uris
        assert "/api/test-gateway/test-stage/test/path/" in uris
        assert priority == 0

    def test_convert_uris_with_match_subpath(self, convertor, mock_release_data):
        """Test _convert_uris with match_subpath"""
        uris, priority = convertor._convert_uris("/test/path", match_subpath=True)
        assert len(uris) == 2
        assert "/api/test-gateway/test-stage/test/path" in uris
        assert f"/api/test-gateway/test-stage/test/path/*{SUBPATH_PARAM_NAME}" in uris
        assert priority < 0  # Should be negative due to MATCH_SUB_PATH_PRIORITY

    def test_convert_uris_with_params(self, convertor, mock_release_data):
        """Test _convert_uris with path parameters"""
        uris, priority = convertor._convert_uris("/test/:id/path", match_subpath=False)
        assert len(uris) == 1
        assert "/api/test-gateway/test-stage/test/:id/path/?" in uris
        assert priority == 0

    def test_convert_uris_with_params_and_match_subpath(self, convertor, mock_release_data):
        # /test/{id}/path -> /test/:id/path/
        uris, priority = convertor._convert_uris("/test/{id}/path", match_subpath=True)
        assert len(uris) == 2
        assert "/api/test-gateway/test-stage/test/:id/path" in uris
        assert f"/api/test-gateway/test-stage/test/:id/path/*{SUBPATH_PARAM_NAME}" in uris
        assert priority < 0  # Should be negative due to MATCH_SUB_PATH_PRIORITY

    def test_convert_uris_with_params_and_no_match_subpath(self, convertor, mock_release_data):
        uris, priority = convertor._convert_uris("/test/{id}/path", match_subpath=False)
        assert len(uris) == 1
        assert "/api/test-gateway/test-stage/test/:id/path/?" in uris
        assert priority == 0

    def test_convert_route_timeout(self, convertor):
        """Test _convert_route_timeout method"""
        # With timeout
        resource_proxy = {"timeout": 60}
        timeout = convertor._convert_route_timeout(resource_proxy)
        assert timeout is not None
        assert isinstance(timeout, Timeout)
        assert timeout.connect == 60
        assert timeout.send == 60
        assert timeout.read == 60

        # Without timeout
        resource_proxy = {}
        timeout = convertor._convert_route_timeout(resource_proxy)
        assert timeout is None

    def test_convert_route_timeout_none(self, convertor):
        """Test _convert_route_timeout method with None"""
        resource_proxy = {}
        timeout = convertor._convert_route_timeout(resource_proxy)
        assert timeout is None

    def test_convert_http_resource_plugins(self, convertor, mock_release_data):
        """Test _convert_http_resource_plugins method"""
        resource = {
            "id": 1,
            "name": "test-resource",
            "contexts": {
                "resource_auth": {
                    "config": json.dumps(
                        {
                            "app_verified_required": True,
                            "auth_verified_required": False,
                            "resource_perm_required": True,
                            "skip_auth_verification": False,
                        }
                    )
                }
            },
        }
        resource_proxy = {"method": "GET", "path": "/backend/path"}

        plugins = convertor._convert_http_resource_plugins(resource, resource_proxy)
        assert "bk-resource-context" in plugins
        assert "bk-proxy-rewrite" in plugins
        assert plugins["bk-resource-context"].bk_resource_id == 1
        assert plugins["bk-resource-context"].bk_resource_name == "test-resource"
        assert plugins["bk-resource-context"].bk_resource_auth == {
            "verified_app_required": True,
            "verified_user_required": False,
            "resource_perm_required": True,
            "skip_user_verification": False,
        }

    def test_build_bk_proxy_rewrite_config_simple(self, convertor, mock_release_data):
        """Test _build_bk_proxy_rewrite_config with simple config"""
        resource_proxy = {"path": "/backend/path", "method": "POST"}
        config = convertor._build_bk_proxy_rewrite_config(resource_proxy)
        assert "uri" in config
        assert config["uri"] == "/backend/path"
        assert config["method"] == "POST"

    def test_build_bk_proxy_rewrite_config_with_match_subpath(self, convertor, mock_release_data):
        """Test _build_bk_proxy_rewrite_config with match_subpath"""
        resource_proxy = {"path": "/backend/path", "match_subpath": True}
        config = convertor._build_bk_proxy_rewrite_config(resource_proxy)
        assert config["match_subpath"] is True
        assert config["subpath_param_name"] == SUBPATH_PARAM_NAME
        assert config["uri"] == f"/backend/path/${{{SUBPATH_PARAM_NAME}}}"

    def test_build_bk_proxy_rewrite_config_with_any_method(self, convertor, mock_release_data):
        """Test _build_bk_proxy_rewrite_config with ANY method"""
        resource_proxy = {"path": "/backend/path", "method": "ANY"}
        config = convertor._build_bk_proxy_rewrite_config(resource_proxy)
        assert "method" not in config

    def test_build_bk_proxy_rewrite_config_with_upstream_uri(self, convertor, mock_release_data):
        # uri should with ${env.varName}
        resource_proxy = {"path": "/api/{env.env}/users/{userId}/profile", "method": "GET"}
        config = convertor._build_bk_proxy_rewrite_config(resource_proxy)
        assert config["uri"] == "/api/test/users/${userId}/profile"
        assert config["method"] == "GET"

    def test_get_release_version_detect_route(self, mock_release_data, backend_service_mapping):
        """Test _get_release_version_detect_route method"""
        convertor = RouteConvertor(
            release_data=mock_release_data,
            backend_service_mapping=backend_service_mapping,
            publish_id=12345,
            revoke_flag=False,
        )
        route = convertor._get_release_version_detect_route()
        assert route.id == "test-gateway.test-stage.-1"
        assert "builtin-mock-release-version" in route.name
        assert route.uris == ["/api/test-gateway/test-stage/__apigw_version"]
        assert route.methods == [HttpMethodEnum.GET]
        assert "bk-mock" in route.plugins
        assert route.timeout is not None
        assert route.timeout.connect == 60

    def test_calculate_match_subpath_route_priority(self, convertor):
        """Test _calculate_match_subpath_route_priority method with various path inputs."""
        test_cases = [
            {"path": "a/b/c", "expected": MATCH_SUB_PATH_PRIORITY + 5},
            {"path": "a/:abc/c", "expected": MATCH_SUB_PATH_PRIORITY + 5},
            {"path": "", "expected": MATCH_SUB_PATH_PRIORITY},
            {"path": "a/abc/c", "expected": MATCH_SUB_PATH_PRIORITY + 7},
            {"path": "test", "expected": MATCH_SUB_PATH_PRIORITY + 4},
            {"path": ":id/:name/:type", "expected": MATCH_SUB_PATH_PRIORITY + 5},
            {"path": "api/:version/users/:id", "expected": MATCH_SUB_PATH_PRIORITY + 13},
            {"path": "/", "expected": MATCH_SUB_PATH_PRIORITY + 1},
            {"path": "api/v1/users/:id/profile", "expected": MATCH_SUB_PATH_PRIORITY + 22},
        ]

        for test_case in test_cases:
            result = convertor._calculate_match_subpath_route_priority(test_case["path"])
            assert result == test_case["expected"], (
                f"Failed for path '{test_case['path']}': expected {test_case['expected']}, got {result}"
            )

    def test_calculate_match_subpath_route_priority_edge_cases(self, convertor):
        """Test edge cases for _calculate_match_subpath_route_priority method."""
        # Test with only colons (should be replaced with 'a')
        # ":::" -> split by "/" -> [":::"] -> replace "::" with "a" -> ["a"] -> join -> "a" -> len = 1
        result = convertor._calculate_match_subpath_route_priority(":::")
        expected = MATCH_SUB_PATH_PRIORITY + 1
        assert result == expected

        # Test with empty segments
        # "a//b" -> split by "/" -> ["a", "", "b"] -> no changes -> join -> "a//b" -> len = 4
        result = convertor._calculate_match_subpath_route_priority("a//b")
        expected = MATCH_SUB_PATH_PRIORITY + 4
        assert result == expected

        # Test with leading and trailing slashes
        # "/a/b/" -> split by "/" -> ["", "a", "b", ""] -> no changes -> join -> "/a/b/" -> len = 5
        result = convertor._calculate_match_subpath_route_priority("/a/b/")
        expected = MATCH_SUB_PATH_PRIORITY + 5
        assert result == expected
