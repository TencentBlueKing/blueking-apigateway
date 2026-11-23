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
from pydantic import ValidationError

from apigateway.biz.resource import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.core.constants import ResourceKindEnum


class TestResourceAuthConfig:
    def test_defaults(self):
        assert ResourceAuthConfig().model_dump() == {
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
            "oauth2_public_client_enabled": False,
            "oauth2_personal_client_enabled": False,
        }

    @pytest.mark.parametrize(
        "oauth2_config",
        [
            {"oauth2_public_client_enabled": True},
            {"oauth2_personal_client_enabled": True},
            {
                "oauth2_public_client_enabled": True,
                "oauth2_personal_client_enabled": True,
            },
        ],
    )
    def test_oauth2_client_requires_user_authentication(self, oauth2_config):
        with pytest.raises(ValidationError, match="require user authentication"):
            ResourceAuthConfig(auth_verified_required=False, **oauth2_config)

    @pytest.mark.parametrize(
        "app_verified_required, resource_perm_required, expected",
        [
            (True, True, True),
            (True, False, False),
            (False, True, False),
            (False, False, False),
        ],
    )
    def test_resource_perm_required_requires_app_verification(
        self, app_verified_required, resource_perm_required, expected
    ):
        config = ResourceAuthConfig(
            app_verified_required=app_verified_required,
            resource_perm_required=resource_perm_required,
        )

        assert config.resource_perm_required is expected


class TestResourceBackendConfig:
    @pytest.mark.parametrize(
        "data, expected, expected_legacy_upstreams, expected_legacy_transform_headers",
        [
            (
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                },
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                },
                None,
                None,
            ),
            (
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                    "legacy_upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [{"host": "http://foo.com", "weight": 10}],
                    },
                    "legacy_transform_headers": {
                        "set": {"x-token": "test"},
                        "delete": ["x-token"],
                    },
                },
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                },
                {
                    "loadbalance": "roundrobin",
                    "hosts": [{"host": "http://foo.com", "weight": 10}],
                },
                {
                    "set": {"x-token": "test"},
                    "delete": ["x-token"],
                },
            ),
        ],
    )
    def test_dict(self, data, expected, expected_legacy_upstreams, expected_legacy_transform_headers):
        config = ResourceBackendConfig.model_validate(data)
        assert config.legacy_upstreams == expected_legacy_upstreams
        assert config.legacy_transform_headers == expected_legacy_transform_headers
        assert config.model_dump() == expected


class TestResourceData:
    @pytest.mark.parametrize(
        "is_public, auth_config, allow_apply_permission, expected",
        [
            (True, {}, True, True),
            (True, {}, False, False),
            (False, {}, True, False),
            (True, {"resource_perm_required": False}, True, False),
            (True, {"app_verified_required": False, "resource_perm_required": True}, True, False),
        ],
    )
    def test_allow_apply_permission_requires_public_and_resource_perm(
        self, is_public, auth_config, allow_apply_permission, expected
    ):
        data = ResourceData(
            name="echo",
            method="GET",
            path="/echo",
            is_public=is_public,
            allow_apply_permission=allow_apply_permission,
            auth_config=ResourceAuthConfig(**auth_config),
            backend_config={"method": "GET", "path": "/echo"},
        )

        assert data.allow_apply_permission is expected

    def test_ai_resource_accepts_backend_without_http_config(self):
        data = ResourceData(
            name="chat",
            kind=ResourceKindEnum.AI.value,
            method="POST",
            path="/chat",
            auth_config=ResourceAuthConfig(),
            backend_config=None,
        )

        assert data.backend_config is None

    @pytest.mark.parametrize(
        "overrides",
        [
            {"method": "GET"},
            {"match_subpath": True},
            {"enable_websocket": True},
            {"backend_config": {"method": "POST", "path": "/chat"}},
        ],
    )
    def test_ai_resource_rejects_standard_proxy_configuration(self, overrides):
        data = {
            "name": "chat",
            "kind": ResourceKindEnum.AI.value,
            "method": "POST",
            "path": "/chat",
            "auth_config": ResourceAuthConfig(),
            "backend_config": None,
        }
        data.update(overrides)

        with pytest.raises(ValidationError):
            ResourceData(**data)

    def test_standard_resource_requires_backend_config(self):
        with pytest.raises(ValidationError):
            ResourceData(
                name="echo",
                method="GET",
                path="/echo",
                auth_config=ResourceAuthConfig(),
                backend_config=None,
            )
