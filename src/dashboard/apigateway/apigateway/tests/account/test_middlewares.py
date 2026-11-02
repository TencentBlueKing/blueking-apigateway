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
import json
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apigateway.account.middlewares import SelfAppCodeAppSecretLoginMiddleware, UserTimezoneMiddleware


class TestSelfAppCodeAppSecretLoginMiddleware:
    @pytest.mark.parametrize(
        "header",
        [
            None,
            "{",
            "{}",
            '{"bk_app_code": "wrong", "bk_app_secret": "app-secret"}',
            '{"bk_app_code": "app-code", "bk_app_secret": "wrong"}',
            '{"bk_app_code": "app-code"}',
            '{"bk_app_secret": "app-secret"}',
        ],
    )
    def test_invalid_credentials_leave_identity_and_csrf_unchanged(self, settings, header):
        settings.BK_APP_CODE, settings.BK_APP_SECRET = "app-code", "app-secret"
        user = SimpleNamespace(is_authenticated=False)
        request = SimpleNamespace(META={}, user=user)
        if header is not None:
            request.META["HTTP_X_BKAPI_AUTHORIZATION"] = header
        middleware = SelfAppCodeAppSecretLoginMiddleware(lambda request: request)
        assert middleware(request) is request
        assert request.user is user
        assert not hasattr(request, "app")
        assert not hasattr(request, "_dont_enforce_csrf_checks")

    @pytest.mark.parametrize("header", ["[]", "null", '"text"', "123"])
    def test_non_object_authorization_does_not_authenticate(self, settings, header):
        settings.BK_APP_CODE, settings.BK_APP_SECRET = "app-code", "app-secret"
        user = SimpleNamespace(is_authenticated=False)
        request = SimpleNamespace(META={"HTTP_X_BKAPI_AUTHORIZATION": header}, user=user)
        assert SelfAppCodeAppSecretLoginMiddleware(lambda request: request)(request) is request
        assert request.user is user
        assert not hasattr(request, "app")
        assert not hasattr(request, "_dont_enforce_csrf_checks")

    @pytest.mark.parametrize("already_authenticated", [False, True])
    def test_valid_credentials_authenticate_without_replacing_authenticated_user(
        self, settings, already_authenticated
    ):
        settings.BK_APP_CODE, settings.BK_APP_SECRET = "app-code", "app-secret"
        user = SimpleNamespace(is_authenticated=already_authenticated, username="existing")
        request = SimpleNamespace(
            META={
                "HTTP_X_BKAPI_AUTHORIZATION": json.dumps({"bk_app_code": "app-code", "bk_app_secret": "app-secret"})
            },
            user=user,
        )
        assert SelfAppCodeAppSecretLoginMiddleware(lambda request: request)(request) is request
        assert request.app.app_code == "app-code"
        assert request._dont_enforce_csrf_checks is True
        if already_authenticated:
            assert request.user is user
        else:
            assert request.user.is_authenticated is True
            assert request.user.username == ""


class TestUserTimezoneMiddleware:
    @pytest.mark.parametrize(
        "user_zone, expected_zone",
        [("Europe/Paris", "Europe/Paris"), ("Invalid/Timezone", "UTC"), ("", "UTC"), (None, "UTC"), (123, "UTC")],
    )
    def test_activates_user_or_default_zone_and_cleans_up(self, settings, user_zone, expected_zone):
        settings.TIME_ZONE = "UTC"
        seen = []
        response = object()

        def get_response(request):
            seen.append(timezone.get_current_timezone_name())
            return response

        middleware = UserTimezoneMiddleware(get_response)
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, time_zone=user_zone, username="user"))
        try:
            assert middleware(request) is response
            assert seen == [expected_zone]
            assert timezone.get_current_timezone_name() == "UTC"
        finally:
            timezone.deactivate()

    def test_next_anonymous_request_does_not_inherit_previous_user_timezone(self, settings):
        settings.TIME_ZONE = "UTC"
        seen = []

        def get_response(request):
            seen.append(timezone.get_current_timezone_name())
            return object()

        middleware = UserTimezoneMiddleware(get_response)
        try:
            middleware(
                SimpleNamespace(user=SimpleNamespace(is_authenticated=True, time_zone="Asia/Tokyo", username="user"))
            )
            middleware(SimpleNamespace(user=SimpleNamespace(is_authenticated=False)))
            assert seen == ["Asia/Tokyo", "UTC"]
            assert timezone.get_current_timezone_name() == "UTC"
        finally:
            timezone.deactivate()
