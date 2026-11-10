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
from django.contrib.auth.models import AnonymousUser

from apigateway.account.middlewares import (
    ApiGatewayJWTAppMiddleware,
    ApiGatewayJWTUserMiddleware,
    SelfAppCodeAppSecretLoginMiddleware,
)
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.tests.utils.testing import get_response_json


@pytest.fixture
def apply_gateway_permission(request_factory, request_to_view, fake_gateway, settings, mocker):
    settings.ENABLE_MULTI_TENANT_MODE = False
    settings.ENABLE_ITSM4_PERMISSION_APPLY = False
    notify = mocker.patch("apigateway.apis.v2.open.views.apply_async_on_commit")

    def apply(app_code="test-app", user_verified=False, username="", app_verified=True, **overrides):
        request = request_factory.post(
            "",
            data={
                "target_app_code": app_code,
                "grant_dimension": "gateway",
                "applicant": "developer",
                "reason": "test application",
            },
            format="json",
        )
        # Exercise the real identity projection after the gateway JWT has been verified.
        request.jwt = SimpleNamespace(
            gateway_name="bk-apigateway",
            payload={
                "app": {"app_code": app_code, "verified": app_verified},
                "user": {"username": username, "verified": user_verified},
            },
        )
        request.user = AnonymousUser()
        request.COOKIES.clear()
        ApiGatewayJWTAppMiddleware(lambda request: None)(request)
        ApiGatewayJWTUserMiddleware(lambda request: None)(request)
        for name, value in overrides.items():
            setattr(request, name, value)
        return request_to_view(
            request,
            view_name="openapi.v2.open.gateway.permissions.apply",
            path_params={"gateway_name": fake_gateway.name},
        )

    return apply, notify


@pytest.mark.parametrize(
    ("app_code", "user_verified", "username", "app_verified"),
    [
        ("test-app", True, "token-owner", True),
        ("test-app", True, "", True),
        ("personal", True, "token-owner", True),
        ("personal", False, "", True),
        ("public", True, "token-owner", True),
        ("public", False, "", True),
        ("test-app", False, "", False),
    ],
)
def test_apply_rejects_user_identity_and_builtin_apps(
    apply_gateway_permission, app_code, user_verified, username, app_verified
):
    apply, notify = apply_gateway_permission
    response = apply(app_code, user_verified, username, app_verified)

    assert response.status_code == 403
    assert not AppPermissionApply.objects.exists()
    assert not AppPermissionRecord.objects.exists()
    notify.assert_not_called()


@pytest.mark.parametrize(("secret", "expected_status"), [("self-secret", 200), ("wrong-secret", 401)])
def test_apply_preserves_authenticated_self_app_calls(
    request_factory, request_to_view, fake_gateway, settings, mocker, secret, expected_status
):
    settings.ENABLE_MULTI_TENANT_MODE = False
    settings.ENABLE_ITSM4_PERMISSION_APPLY = False
    settings.BK_APP_CODE = "dashboard-app"
    settings.BK_APP_SECRET = "self-secret"
    notify = mocker.patch("apigateway.apis.v2.open.views.apply_async_on_commit")
    request = request_factory.post(
        "",
        data={"target_app_code": "dashboard-app", "grant_dimension": "gateway", "applicant": "developer"},
        format="json",
        HTTP_X_BKAPI_AUTHORIZATION=json.dumps({"bk_app_code": "dashboard-app", "bk_app_secret": secret}),
    )
    request.user = AnonymousUser()
    request.COOKIES.clear()
    SelfAppCodeAppSecretLoginMiddleware(lambda request: None)(request)
    response = request_to_view(
        request,
        view_name="openapi.v2.open.gateway.permissions.apply",
        path_params={"gateway_name": fake_gateway.name},
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert AppPermissionApply.objects.get().bk_app_code == "dashboard-app"
        assert AppPermissionRecord.objects.get().bk_app_code == "dashboard-app"
        notify.assert_called_once()
    else:
        assert not AppPermissionApply.objects.exists()
        assert not AppPermissionRecord.objects.exists()
        notify.assert_not_called()


@pytest.mark.parametrize("username", ["", "unverified-user"])
def test_apply_allows_app_identity_without_verified_user(apply_gateway_permission, username):
    apply, notify = apply_gateway_permission
    response = apply(username=username)

    assert response.status_code == 200
    result = get_response_json(response)
    application = AppPermissionApply.objects.get(apply_record_id=result["data"]["record_id"])
    assert application.bk_app_code == "test-app"
    assert application.applied_by == "developer"
    assert AppPermissionRecord.objects.get().bk_app_code == "test-app"
    notify.assert_called_once()


def test_apply_uses_jwt_user_even_when_request_user_is_authenticated(apply_gateway_permission):
    apply, notify = apply_gateway_permission
    response = apply(user=SimpleNamespace(username="cookie-user", is_active=True, is_authenticated=True))

    assert response.status_code == 200
    assert AppPermissionApply.objects.get().applied_by == "developer"
    notify.assert_called_once()
