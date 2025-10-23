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

from apigateway.controller.uri_render import UpstreamURIRender, URIRender, env_render


class TestEnvRender:
    """Test environment variable rendering"""

    def test_env_render_with_vars(self):
        """Test rendering with environment variables"""
        source = "/api/{env.stage}/{env.version}/users"
        vars_dict = {"stage": "prod", "version": "v1"}
        result = env_render(source, vars_dict)
        assert result == "/api/prod/v1/users"

    def test_env_render_without_env_vars(self):
        """Test rendering without environment variables"""
        source = "/api/users/{userId}"
        vars_dict = {"stage": "prod"}
        result = env_render(source, vars_dict)
        assert result == "/api/users/{userId}"

    def test_env_render_with_missing_vars(self):
        """Test rendering with missing environment variables"""
        source = "/api/{env.stage}/{env.version}/users"
        vars_dict = {"stage": "dev"}
        result = env_render(source, vars_dict)
        assert result == "/api/dev/{env.version}/users"

    def test_env_render_empty_vars(self):
        """Test rendering with empty vars dictionary"""
        source = "/api/{env.stage}/users"
        result = env_render(source, {})
        assert result == "/api/{env.stage}/users"

    def test_env_render_no_env_vars_in_source(self):
        """Test rendering when source has no environment variables"""
        source = "/api/users"
        vars_dict = {"stage": "prod"}
        result = env_render(source, vars_dict)
        assert result == "/api/users"

    def test_env_render_multiple_same_var(self):
        """Test rendering with same variable appearing multiple times"""
        source = "/api/{env.stage}/users/{env.stage}"
        vars_dict = {"stage": "test"}
        result = env_render(source, vars_dict)
        assert result == "/api/test/users/test"


class TestURIRender:
    """Test URIRender class"""

    def test_render_with_env_and_path_params(self):
        """Test rendering with both environment variables and path parameters"""
        renderer = URIRender()
        source = "/api/{env.stage}/{env.version}/users/{userId}/profile"
        vars_dict = {"stage": "prod", "version": "v1"}
        result = renderer.render(source, vars_dict)
        assert result == "/api/prod/v1/users/:userId/profile"

    def test_render_path_params_only(self):
        """Test rendering with only path parameters"""
        renderer = URIRender()
        source = "/api/users/{userId}/orders/{orderId}"
        result = renderer.render(source, {})
        assert result == "/api/users/:userId/orders/:orderId"

    def test_render_env_vars_only(self):
        """Test rendering with only environment variables"""
        renderer = URIRender()
        source = "/api/{env.stage}/users"
        vars_dict = {"stage": "dev"}
        result = renderer.render(source, vars_dict)
        assert result == "/api/dev/users"

    def test_render_no_variables(self):
        """Test rendering without any variables"""
        renderer = URIRender()
        source = "/api/users"
        result = renderer.render(source, {})
        assert result == "/api/users"

    def test_render_complex_path(self):
        """Test rendering with complex path"""
        renderer = URIRender()
        source = "/api/{env.region}/{env.stage}/v{env.version}/users/{userId}/posts/{postId}/comments"
        vars_dict = {"region": "us-west", "stage": "production", "version": "2"}
        result = renderer.render(source, vars_dict)
        assert result == "/api/us-west/production/v2/users/:userId/posts/:postId/comments"

    def test_render_with_missing_env_vars(self):
        """Test rendering with missing environment variables leaves them as-is"""
        renderer = URIRender()
        source = "/api/{env.stage}/users/{userId}"
        vars_dict = {}
        result = renderer.render(source, vars_dict)
        # env vars not replaced, but path params are converted
        assert result == "/api/{env.stage}/users/:userId"


class TestUpstreamURIRender:
    """Test UpstreamURIRender class"""

    def test_render_with_env_and_path_params(self):
        """Test upstream rendering with both environment variables and path parameters"""
        renderer = UpstreamURIRender()
        source = "/api/{env.stage}/{env.version}/users/{userId}/profile"
        vars_dict = {"stage": "prod", "version": "v1"}
        result = renderer.render(source, vars_dict)
        assert result == "/api/prod/v1/users/${userId}/profile"

    def test_render_path_params_only(self):
        """Test upstream rendering with only path parameters"""
        renderer = UpstreamURIRender()
        source = "/api/users/{userId}/orders/{orderId}"
        result = renderer.render(source, {})
        assert result == "/api/users/${userId}/orders/${orderId}"

    def test_render_env_vars_only(self):
        """Test upstream rendering with only environment variables"""
        renderer = UpstreamURIRender()
        source = "/api/{env.stage}/users"
        vars_dict = {"stage": "dev"}
        result = renderer.render(source, vars_dict)
        assert result == "/api/dev/users"

    def test_render_missing_env_vars(self):
        """Test upstream rendering with only environment variables"""
        renderer = UpstreamURIRender()
        source = "/api/{env.stage}/users/{userId}"
        vars_dict = {}
        result = renderer.render(source, vars_dict)
        assert result == "/api/{env.stage}/users/${userId}"

    def test_render_no_variables(self):
        """Test upstream rendering without any variables"""
        renderer = UpstreamURIRender()
        source = "/api/users"
        result = renderer.render(source, {})
        assert result == "/api/users"

    def test_render_complex_path(self):
        """Test upstream rendering with complex path"""
        renderer = UpstreamURIRender()
        source = "/api/{env.region}/{env.stage}/v{env.version}/users/{userId}/posts/{postId}"
        vars_dict = {"region": "eu-central", "stage": "staging", "version": "3"}
        result = renderer.render(source, vars_dict)
        assert result == "/api/eu-central/staging/v3/users/${userId}/posts/${postId}"
