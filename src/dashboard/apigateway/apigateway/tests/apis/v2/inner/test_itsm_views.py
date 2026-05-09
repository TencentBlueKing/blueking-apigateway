# -*- coding: utf-8 -*-
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
from unittest import mock


class TestItsmCallbackApi:
    def _build_callback_data(self, callback_token="cb-token"):
        data = {
            "ticket": {
                "id": "itsm-ticket-001",
                "approve_result": True,
                "form_data": {
                    "apply_record_id": 1,
                    "grant_dimension": "gateway",
                },
            }
        }
        if callback_token is not None:
            data["callback_token"] = callback_token
        return data

    def test_reject_when_callback_token_empty(self, request_view, settings, mocker):
        settings.BK_ITSM4_CALLBACK_ALLOWED_APP_CODES = ["bk-itsm4"]
        mocker.patch("apigateway.biz.bk_itsm.bk_itsm.ItsmCallbackResultHandler.handle")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.itsm.callback",
            app=mock.MagicMock(app_code="bk-itsm4"),
            data=self._build_callback_data(callback_token=""),
            format="json",
        )

        assert response.status_code == 400

    def test_reject_when_callback_token_missing(self, request_view, settings, mocker):
        settings.BK_ITSM4_CALLBACK_ALLOWED_APP_CODES = ["bk-itsm4"]
        mocker.patch("apigateway.biz.bk_itsm.bk_itsm.ItsmCallbackResultHandler.handle")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.itsm.callback",
            app=mock.MagicMock(app_code="bk-itsm4"),
            data=self._build_callback_data(callback_token=None),
            format="json",
        )

        assert response.status_code == 400

    def test_reject_invalid_source_app(self, request_view, settings, mocker):
        settings.BK_ITSM4_CALLBACK_ALLOWED_APP_CODES = ["bk-itsm4"]
        mocker.patch("apigateway.biz.bk_itsm.bk_itsm.ItsmCallbackResultHandler.handle")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.itsm.callback",
            app=mock.MagicMock(app_code="unauthorized-app"),
            data=self._build_callback_data(),
            format="json",
        )

        assert response.status_code == 400

    def test_allow_when_missing_tenant_header_in_multi_tenant_mode(self, request_view, settings, mocker):
        settings.ENABLE_MULTI_TENANT_MODE = True
        settings.BK_ITSM4_CALLBACK_ALLOWED_APP_CODES = ["bk-itsm4"]
        mock_handle = mocker.patch("apigateway.biz.bk_itsm.bk_itsm.ItsmCallbackResultHandler.handle")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.itsm.callback",
            app=mock.MagicMock(app_code="bk-itsm4"),
            data=self._build_callback_data(),
            format="json",
        )

        assert response.status_code == 200
        assert mock_handle.call_count == 1

    def test_allow_with_tenant_header_in_multi_tenant_mode(self, request_view, settings, mocker):
        settings.ENABLE_MULTI_TENANT_MODE = True
        settings.BK_ITSM4_CALLBACK_ALLOWED_APP_CODES = ["bk-itsm4"]
        mock_handle = mocker.patch("apigateway.biz.bk_itsm.bk_itsm.ItsmCallbackResultHandler.handle")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.itsm.callback",
            app=mock.MagicMock(app_code="bk-itsm4"),
            data=self._build_callback_data(),
            format="json",
            HTTP_X_BK_TENANT_ID="tenant-001",
        )

        assert response.status_code == 200
        assert mock_handle.call_count == 1
