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

from environ import Env

from apigateway.conf.utils import (
    get_default_feature_flags,
    get_doc_links,
    get_frontend_env_vars,
    get_plugin_metadata_config,
)


def test_get_plugin_metadata_config_uses_local_concurrency_policy():
    config = get_plugin_metadata_config(Env())

    assert config["bk-concurrency-limit"]["policy"] == "local"


def test_get_default_feature_flags_mcp_server_oauth2_personal_client(monkeypatch):
    env = Env()
    kwargs = {
        "enable_bk_notice": False,
        "enable_multi_tenant_mode": False,
        "ai_open_api_base_url": "",
        "enable_gateway_operation_status": False,
        "enable_run_data_metrics": False,
        "enable_itsm4_permission_apply": False,
    }

    flags = get_default_feature_flags(env, **kwargs)
    assert flags["ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT"] is True

    monkeypatch.setenv("FEATURE_FLAG_ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT", "false")
    flags = get_default_feature_flags(env, **kwargs)
    assert flags["ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT"] is False


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


def test_get_doc_links_includes_personal_token():
    links = get_doc_links("1.24.0", "https://docs.example.com", "ZH")

    assert (
        links["PERSONAL_TOKEN"]
        == "https://docs.example.com/markdown/ZH/APIGateway/1.24/UserGuide/Explanation/personal-token.md"
    )

    en_links = get_doc_links("1.24.0", "https://docs.example.com", "EN")
    assert (
        en_links["PERSONAL_TOKEN"]
        == "https://docs.example.com/markdown/EN/APIGateway/1.24/UserGuide/Explanation/personal-token.md"
    )
