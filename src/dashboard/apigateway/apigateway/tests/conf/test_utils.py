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
from django.core.exceptions import ImproperlyConfigured
from environ import Env

from apigateway.conf.utils import get_frontend_env_vars, get_sdk_generation_settings


def test_get_sdk_generation_settings_uses_common_defaults():
    settings = get_sdk_generation_settings(Env(), bk_api_url_tmpl="https://bkapi.example.com/{api_name}")

    assert settings["enabled_languages"] == ["python", "java", "go", "javascript", "rust"]
    assert settings["server_url_template"] == "https://bkapi.example.com/{gateway_name}/{stage_name}"
    assert settings["generator_version"] == "7.23.0"


@pytest.mark.parametrize(
    "languages",
    [
        "golang",
        "ruby",
        "python,,go",
        "python,python",
    ],
)
def test_get_sdk_generation_settings_rejects_invalid_languages_at_settings_construction(monkeypatch, languages):
    monkeypatch.setenv("BK_SDK_LANGUAGES", languages)

    with pytest.raises(ImproperlyConfigured, match="BK_SDK_LANGUAGES"):
        get_sdk_generation_settings(Env(), bk_api_url_tmpl="https://bkapi.example.com/{api_name}")


def test_get_frontend_env_vars_includes_paas_developer_center_link(monkeypatch):
    monkeypatch.setenv("BK_USER_URL", "https://user.example.com")

    env_vars = get_frontend_env_vars(
        env=Env(),
        edition="ce",
        bk_app_code="bk-apigateway",
        default_test_app_code="demo-app",
        bk_api_url_tmpl="https://bkapi.example.com/api/{api_name}",
        bk_component_api_url="https://components.example.com",
        dashboard_fe_url="https://dashboard-fe.example.com",
        dashboard_url="https://dashboard.example.com",
        csrf_cookie_name="csrftoken",
        csrf_cookie_domain=".example.com",
        bk_apigateway_version="1.22.0",
        bk_docs_url_prefix="https://docs.example.com",
        bk_login_url="https://login.example.com",
        bk_sdk_languages=["python"],
        bk_paas3_url="https://paas.example.com/",
    )

    assert env_vars["PAAS_DEVELOPER_CENTER_LINK"] == "https://paas.example.com/developer-center"
    assert env_vars["PAAS_APP_CREATE_LINK"] == "https://paas.example.com/developer-center/app/create"
    assert env_vars["BK_USER_PERSONAL_CENTER_LINK"] == "https://user.example.com/personal-center"
