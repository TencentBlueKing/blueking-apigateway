# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import copy

import pytest

from apigateway.apps.esb.component.convertor import Component, ComponentConvertor
from apigateway.common.error_codes import APIError


class TestComponent:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.component = Component.parse_obj(
            {
                "id": None,
                "method": "GET",
                "path": "/echo/",
                "name": "echo",
                "full_path": "/backend/echo/",
                "is_public": False,
                "description": "test",
                "permission_level": "unlimited",
                "verified_user_required": False,
                "system_name": "DEMO",
                "binding_resource_id": 1,
            }
        )

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "id": None,
                    "method": "GET",
                    "path": "/echo/",
                    "name": "echo",
                    "full_path": "/backend/echo/",
                    "is_public": False,
                    "description": "test",
                    "permission_level": "unlimited",
                    "verified_user_required": False,
                    "system_name": "DEMO",
                    "binding_resource_id": 1,
                    "binding_resource_name": "demo_echo",
                },
                {
                    "id": 1,
                    "method": "GET",
                    "path": "/echo/",
                    "match_subpath": False,
                    "name": "demo_echo",
                    "description": "test",
                    "is_public": False,
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/backend/echo/",
                            "match_subpath": False,
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "app_verified_required": False,
                        "resource_perm_required": False,
                        "auth_verified_required": False,
                    },
                    "allow_apply_permission": False,
                    "labels": ["DEMO"],
                    "disabled_stages": [],
                    "extend_data": {
                        "system_name": "DEMO",
                        "component_id": None,
                        "component_name": "echo",
                        "component_method": "GET",
                        "component_path": "/echo/",
                        "component_permission_level": "unlimited",
                    },
                },
            )
        ],
    )
    def test_to_resource(self, data, expected):
        component = Component.parse_obj(data)
        assert component.to_resource() == expected

    @pytest.mark.parametrize(
        "method, expected",
        [
            ("GET", "GET"),
            ("", "ANY"),
            ("POST", "POST"),
            ("DELETE", "DELETE"),
            ("PUT", "PUT"),
        ],
    )
    def test_resource_method(self, mocker, method, expected):
        mocker.patch.object(self.component, "method", new_callable=mocker.PropertyMock(return_value=method))
        assert self.component.resource_method == expected

    @pytest.mark.parametrize(
        "id_, method, path, expected",
        [
            (1, "", "", "1"),
            (0, "GET", "/echo/", "GET:/echo/"),
        ],
    )
    def test_component_key(self, mocker, id_, method, path, expected):
        mocker.patch.object(self.component, "id", new_callable=mocker.PropertyMock(return_value=id_))
        mocker.patch.object(self.component, "method", new_callable=mocker.PropertyMock(return_value=method))
        mocker.patch.object(self.component, "path", new_callable=mocker.PropertyMock(return_value=path))

        assert self.component.component_key == expected

    def test_component_key_error(self, mocker):
        mocker.patch.object(self.component, "id", new_callable=mocker.PropertyMock(return_value=0))
        mocker.patch.object(self.component, "method", new_callable=mocker.PropertyMock(return_value=""))
        mocker.patch.object(self.component, "path", new_callable=mocker.PropertyMock(return_value=""))

        with pytest.raises(ValueError):
            self.component.component_key


class TestComponentConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.convertor = ComponentConvertor()

    def test_get_synchronized_components(self, mocker, settings, faker):
        settings.BK_COMPONENT_API_INNER_URL = faker.uri()

        mock_get_client_by_usename = mocker.patch(
            "apigateway.apps.esb.component.convertor.get_client_by_username",
            return_value=mocker.MagicMock(
                **{"esb.get_synchronized_components.return_value": {"result": True, "data": [{"id": 1}]}}
            ),
        )

        result = self.convertor._get_synchronized_components()
        assert result == [{"id": 1}]
        mock_get_client_by_usename.assert_called_once_with("admin", endpoint=settings.BK_COMPONENT_API_INNER_URL)

    @pytest.mark.parametrize(
        "components, parsed_components, expected",
        [
            (
                [
                    {
                        "id": None,
                        "method": "GET",
                        "path": "/echo/",
                        "name": "echo",
                        "full_path": "/backend/echo/",
                        "is_public": False,
                        "description": "test",
                        "permission_level": "unlimited",
                        "verified_user_required": False,
                        "system_name": "DEMO",
                        "binding_resource_id": 1,
                    }
                ],
                [
                    Component(
                        id=None,
                        method="GET",
                        path="/echo/",
                        name="echo",
                        full_path="/backend/echo/",
                        is_public=False,
                        description="test",
                        permission_level="unlimited",
                        verified_user_required=False,
                        system_name="DEMO",
                        binding_resource_id=1,
                        binding_resource_name="demo_echo",
                    )
                ],
                [
                    {
                        "id": 1,
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": False,
                        "name": "demo_echo",
                        "description": "test",
                        "is_public": False,
                        "proxy_type": "http",
                        "proxy_configs": {
                            "http": {
                                "method": "GET",
                                "path": "/backend/echo/",
                                "match_subpath": False,
                                "timeout": 0,
                                "upstreams": {},
                                "transform_headers": {},
                            }
                        },
                        "auth_config": {
                            "app_verified_required": False,
                            "resource_perm_required": False,
                            "auth_verified_required": False,
                        },
                        "allow_apply_permission": False,
                        "labels": ["DEMO"],
                        "disabled_stages": [],
                        "extend_data": {
                            "system_name": "DEMO",
                            "component_id": None,
                            "component_name": "echo",
                            "component_method": "GET",
                            "component_path": "/echo/",
                            "component_permission_level": "unlimited",
                        },
                    }
                ],
            )
        ],
    )
    def test_to_resources(self, mocker, components, parsed_components, expected):
        mocker.patch.object(self.convertor, "_get_synchronized_components", return_value=components)
        mock_validate_components = mocker.patch.object(self.convertor, "_validate_components")
        mock_enrich_resource_id = mocker.patch.object(self.convertor, "_enrich_resource_id")

        assert self.convertor.to_resources() == expected
        mock_validate_components.assert_called_once_with(components)
        mock_enrich_resource_id.assert_called_once_with(parsed_components)

    @pytest.mark.parametrize(
        "components, will_error",
        [
            (
                [
                    {
                        "method": "",
                        "path": "/echo/",
                    },
                    {
                        "method": "GET",
                        "path": "/echo/get/",
                    },
                ],
                False,
            ),
            (
                [
                    {
                        "method": "GET",
                        "path": "/echo/",
                    },
                    {
                        "method": "POST",
                        "path": "/echo/",
                    },
                ],
                False,
            ),
            (
                [
                    {
                        "method": "GET",
                        "path": "/echo/",
                    },
                    {
                        "method": "GET",
                        "path": "/echo/get/",
                    },
                    {
                        "method": "",
                        "path": "/echo/",
                    },
                ],
                True,
            ),
        ],
    )
    def test_validate_components(self, components, will_error):
        if will_error:
            with pytest.raises(APIError):
                self.convertor._validate_components(components)
            return

        copied_components = copy.deepcopy(components)
        assert self.convertor._validate_components(components) is None
        # components 没有发生变化
        assert components == copied_components

    @pytest.mark.parametrize(
        "components, mock_component_key_to_resource_id, expected",
        [
            (
                [
                    Component(
                        id=None,
                        method="GET",
                        path="/echo/",
                        name="echo",
                        full_path="/backend/echo/",
                        is_public=False,
                        description="test",
                        permission_level="unlimited",
                        verified_user_required=False,
                        system_name="DEMO",
                        binding_resource_id=None,
                        binding_resource_name="demo_echo",
                    )
                ],
                {
                    "GET:/echo/": 10,
                    "1": 11,
                },
                [
                    Component(
                        id=None,
                        method="GET",
                        path="/echo/",
                        name="echo",
                        full_path="/backend/echo/",
                        is_public=False,
                        description="test",
                        permission_level="unlimited",
                        verified_user_required=False,
                        system_name="DEMO",
                        binding_resource_id=10,
                        binding_resource_name="demo_echo",
                    )
                ],
            ),
            (
                [
                    Component(
                        id=10,
                        method="GET",
                        path="/echo/",
                        name="echo",
                        full_path="/backend/echo/",
                        is_public=False,
                        description="test",
                        permission_level="unlimited",
                        verified_user_required=False,
                        system_name="DEMO",
                        resource_id=None,
                        binding_resource_name="demo_echo",
                    )
                ],
                {
                    "10": 10,
                    "GET:/echo/": 11,
                },
                [
                    Component(
                        id=10,
                        method="GET",
                        path="/echo/",
                        name="echo",
                        full_path="/backend/echo/",
                        is_public=False,
                        description="test",
                        permission_level="unlimited",
                        verified_user_required=False,
                        system_name="DEMO",
                        binding_resource_id=10,
                        binding_resource_name="demo_echo",
                    )
                ],
            ),
        ],
    )
    def test_enrich_resource_id(self, mocker, components, mock_component_key_to_resource_id, expected):
        mocker.patch(
            (
                "apigateway.apps.esb.component.convertor."
                "ComponentResourceBinding.objects.get_component_key_to_resource_id"
            ),
            return_value=mock_component_key_to_resource_id,
        )
        result = self.convertor._enrich_resource_id(components)
        assert result == expected
