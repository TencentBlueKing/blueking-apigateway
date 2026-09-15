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
from environ import Env

from apigateway.apis.web.setting.views import FeatureFlagListApi
from apigateway.conf.utils import get_default_feature_flags
from apigateway.tests.utils.testing import get_response_json


class TestFeatureFlagListApi:
    @pytest.mark.parametrize(
        "is_superuser, expected",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_list(self, settings, request_factory, mocker, faker, is_superuser, expected):
        settings.DEFAULT_FEATURE_FLAG = {"MENU_ITEM_ESB_API": True, "MENU_ITEM_ESB_API_DOC": True}
        mocker.patch(
            "apigateway.apis.web.setting.views.UserFeatureFlag.objects.get_feature_flags",
            return_value={faker.color_name(): False},
        )

        # user is not suerperuser
        request = request_factory.get("")
        request.user = mocker.MagicMock(username=faker.color_name(), is_superuser=is_superuser)
        view = FeatureFlagListApi.as_view()
        response = view(request)
        result = get_response_json(response)
        assert len(result["data"]) == 3
        assert settings.DEFAULT_FEATURE_FLAG == {"MENU_ITEM_ESB_API": True, "MENU_ITEM_ESB_API_DOC": True}
        assert result["data"]["MENU_ITEM_ESB_API"] == expected
        assert result["data"]["MENU_ITEM_ESB_API_DOC"] is True


@pytest.mark.parametrize("env_value, expected", [(None, False), ("false", False), ("true", True)])
def test_resource_path_conflict_flag_rendering(monkeypatch, settings, request_factory, mocker, env_value, expected):
    env_name = "FEATURE_FLAG_ENABLE_RESOURCE_PATH_CONFLICT_CHECK"
    monkeypatch.delenv(env_name, raising=False)
    if env_value is not None:
        monkeypatch.setenv(env_name, env_value)
    settings.DEFAULT_FEATURE_FLAG = get_default_feature_flags(
        Env(),
        enable_bk_notice=False,
        enable_multi_tenant_mode=False,
        ai_open_api_base_url="",
        enable_gateway_operation_status=False,
        enable_run_data_metrics=False,
        enable_itsm4_permission_apply=False,
    )
    mocker.patch("apigateway.apis.web.setting.views.UserFeatureFlag.objects.get_feature_flags", return_value={})
    request = request_factory.get("")
    request.user = mocker.MagicMock(username="tester", is_superuser=False)
    response = FeatureFlagListApi.as_view()(request)
    assert get_response_json(response)["data"]["ENABLE_RESOURCE_PATH_CONFLICT_CHECK"] is expected
