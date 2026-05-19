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
import pytest

from apigateway.apis.v2.inner.serializers import MonitorCallbackInputSLZ


class TestMonitorCallbackInputSLZ:
    """参考 V1 的 TestMonitorCallbackSLZ，测试 V2 的序列化器 token 校验"""

    @pytest.mark.parametrize(
        "params, expected_is_valid",
        [
            ({}, False),
            ({"token": ""}, False),
            ({"token": "error"}, False),
            ({"token": "my-token"}, True),
        ],
    )
    def test_validate(self, settings, params, expected_is_valid):
        settings.BKMONITOR_CALLBACK_TOKEN = "my-token"

        slz = MonitorCallbackInputSLZ(data=params)
        result = slz.is_valid(raise_exception=False)
        assert result == expected_is_valid


class TestAlarmCallbackApi:
    @pytest.fixture()
    def setup_settings(self, settings):
        settings.BKMONITOR_CALLBACK_TOKEN = "my-token"

    @pytest.mark.parametrize(
        "alarm_type",
        ["resource_backend", "app_request", "nginx_error"],
    )
    def test_callback_success(self, request_view, setup_settings, mocker, alarm_type):
        mock_task = mocker.patch(f"apigateway.apis.v2.inner.monitor_views.monitor_{alarm_type}.apply_async")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.monitor.alarm_callback",
            path_params={"alarm_type": alarm_type},
            data={"alert_name": "test-alert"},
            format="json",
            QUERY_STRING="token=my-token",
        )

        assert response.status_code == 200
        assert response.json() == {"code": 0, "result": True, "message": "OK", "data": None}
        mock_task.assert_called_once()

    def test_reject_when_token_missing(self, request_view, setup_settings, mocker):
        mocker.patch("apigateway.apis.v2.inner.monitor_views.monitor_resource_backend.apply_async")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.monitor.alarm_callback",
            path_params={"alarm_type": "resource_backend"},
            data={"alert_name": "test-alert"},
            format="json",
        )

        assert response.status_code == 400

    def test_reject_when_token_empty(self, request_view, setup_settings, mocker):
        mocker.patch("apigateway.apis.v2.inner.monitor_views.monitor_resource_backend.apply_async")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.monitor.alarm_callback",
            path_params={"alarm_type": "resource_backend"},
            data={"alert_name": "test-alert"},
            format="json",
            QUERY_STRING="token=",
        )

        assert response.status_code == 400

    def test_reject_when_token_invalid(self, request_view, setup_settings, mocker):
        mocker.patch("apigateway.apis.v2.inner.monitor_views.monitor_resource_backend.apply_async")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.monitor.alarm_callback",
            path_params={"alarm_type": "resource_backend"},
            data={"alert_name": "test-alert"},
            format="json",
            QUERY_STRING="token=wrong-token",
        )

        assert response.status_code == 400

    def test_reject_when_alarm_type_invalid(self, request_view, setup_settings, mocker):
        mocker.patch("apigateway.apis.v2.inner.monitor_views.monitor_resource_backend.apply_async")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.monitor.alarm_callback",
            path_params={"alarm_type": "invalid_type"},
            data={"alert_name": "test-alert"},
            format="json",
            QUERY_STRING="token=my-token",
        )

        assert response.status_code == 400
