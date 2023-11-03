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
from unittest import mock

import pytest

from apigateway.core.api_auth import APIAuthConfig, UserAuthConfig


class TestUserAuthConfig:
    @pytest.fixture(autouse=True)
    def fake_gateway_user_auth_configs(self, settings):
        settings.API_USER_AUTH_CONFIGS = {
            "default": {
                "user_type": "default",
                "from_bk_token": True,
                "from_bk_username": False,
            }
        }

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "user_auth_type": "default",
                },
                {
                    "user_auth_type": "default",
                    "rtx_conf": {},
                    "uin_conf": {},
                    "user_conf": {},
                },
            ),
            (
                {
                    "user_auth_type": "default",
                    "rtx_conf": {"a": "b"},
                    "uin_conf": {"c": "d"},
                    "user_conf": {"e": "f"},
                },
                {
                    "user_auth_type": "default",
                    "rtx_conf": {"a": "b"},
                    "uin_conf": {"c": "d"},
                    "user_conf": {"e": "f"},
                },
            ),
        ],
    )
    def test_init(self, data, expected):
        result = UserAuthConfig.parse_obj(data)
        assert result.dict() == expected

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "user_auth_type": "default",
                    "user_conf": {
                        "from_bk_token": False,
                    },
                },
                {
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": False,
                        "from_bk_username": False,
                    }
                },
            ),
        ],
    )
    def test_config(self, data, expected):
        assert UserAuthConfig.parse_obj(data).config == expected

    @pytest.mark.parametrize(
        "api_user_auth_configs, user_auth_type, expected",
        [
            (
                {
                    "test": {
                        "user_type": "rtx",
                    },
                },
                "test",
                "rtx_conf",
            ),
            (
                {
                    "test": {
                        "user_type": "uin",
                    },
                },
                "test",
                "uin_conf",
            ),
            (
                {
                    "test": {
                        "user_type": "default",
                    },
                },
                "test",
                "user_conf",
            ),
        ],
    )
    def test_get_user_config_key(self, settings, api_user_auth_configs, user_auth_type, expected):
        settings.API_USER_AUTH_CONFIGS = api_user_auth_configs

        assert UserAuthConfig(user_auth_type=user_auth_type)._get_user_config_key() == expected

    def test_get_default_user_config(self):
        result = UserAuthConfig(user_auth_type="default")._get_default_user_config()
        assert result == {
            "user_type": "default",
            "from_bk_token": True,
            "from_bk_username": False,
        }


class TestAPIAuthConfig:
    @pytest.mark.parametrize(
        "data, mock_user_config, expected",
        [
            (
                {
                    "user_auth_type": "default",
                    "api_type": 0,
                    "unfiltered_sensitive_keys": ["bk_token"],
                    "allow_update_api_auth": True,
                    "rtx_conf": {},
                    "uin_conf": {},
                    "user_conf": {
                        "from_bk_token": True,
                        "from_bk_username": False,
                    },
                },
                {
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": False,
                        "from_bk_username": True,
                    }
                },
                {
                    "user_auth_type": "default",
                    "api_type": 0,
                    "unfiltered_sensitive_keys": ["bk_token"],
                    "allow_update_api_auth": True,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": False,
                        "from_bk_username": True,
                    },
                },
            ),
            (
                {
                    "user_auth_type": "default",
                    "api_type": 0,
                    "unfiltered_sensitive_keys": ["bk_token"],
                    "allow_update_api_auth": True,
                    "include_system_headers": ["X-Bkapi-App"],
                    "allow_auth_from_params": False,
                    "rtx_conf": {},
                    "uin_conf": {},
                    "user_conf": {
                        "from_bk_token": True,
                        "from_bk_username": False,
                    },
                },
                {
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": False,
                        "from_bk_username": True,
                    }
                },
                {
                    "user_auth_type": "default",
                    "api_type": 0,
                    "unfiltered_sensitive_keys": ["bk_token"],
                    "allow_update_api_auth": True,
                    "allow_auth_from_params": False,
                    "include_system_headers": ["X-Bkapi-App"],
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": False,
                        "from_bk_username": True,
                    },
                },
            ),
        ],
    )
    def test_config(self, mocker, data, mock_user_config, expected):
        mocker.patch(
            "apigateway.core.api_auth.UserAuthConfig.config",
            new_callable=mock.PropertyMock(return_value=mock_user_config),
        )
        result = APIAuthConfig.parse_obj(data).config
        assert result == expected
