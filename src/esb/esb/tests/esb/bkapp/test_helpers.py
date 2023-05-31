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
import pytest
from ddf import G

from esb.bkapp.helpers import AppSecureInfo, BKAuthHelper
from esb.bkcore.models import AppAccount

pytestmark = pytest.mark.django_db


class TestAppSecureInfo:
    def test_get_by_app_code(self, faker):
        app1 = faker.unique.pystr()
        app2 = faker.unique.pystr()

        G(AppAccount, app_code=app1, app_token="app1-secret")

        assert AppSecureInfo.get_by_app_code(app1) == {"app_code": app1, "secure_key_list": ["app1-secret"]}
        assert AppSecureInfo.get_by_app_code(app2) is None


class TestBKAuthHelper:
    @pytest.mark.parametrize(
        "app_code, mock_result, expected",
        [
            (
                "app-error",
                {"result": False, "message": "error"},
                [],
            ),
            (
                "app-secret-not-exist",
                {"result": True, "data": [], "message": "ok"},
                [],
            ),
            (
                "app",
                {"result": True, "data": [{"bk_app_secret": "secret"}]},
                ["secret"],
            ),
            (
                "app-another",
                {"result": True, "data": [{"bk_app_secret": "another-secret"}]},
                ["another-secret"],
            ),
        ],
    )
    def test_list_app_secrets(self, settings, mocker, faker, app_code, mock_result, expected):
        settings.BK_AUTH_ENABLED = True

        mocker.patch(
            "components.bk.apisv2.bk_auth.list_app_secrets.ListAppSecrets.invoke",
            return_value=mock_result,
        )

        app_secrets, _ = BKAuthHelper.list_app_secrets(app_code)
        assert app_secrets == expected

    @pytest.mark.parametrize(
        "app_code, mock_result, expected",
        [
            (
                "app-error",
                {"result": False, "message": "error"},
                False,
            ),
            (
                "app-match",
                {"result": True, "data": {"is_match": True}, "message": "ok"},
                True,
            ),
            (
                "app-not-match",
                {"result": True, "data": {"is_match": False}, "message": "error"},
                False,
            ),
        ],
    )
    def test_verify_app_secret(self, settings, mocker, faker, app_code, mock_result, expected):
        settings.BK_AUTH_ENABLED = True

        mocker.patch(
            "components.bk.apisv2.bk_auth.verify_app_secret.VerifyAppSecret.invoke",
            return_value=mock_result,
        )

        verified, _ = BKAuthHelper.verify_app_secret(app_code, faker.uuid4())
        assert verified == expected
