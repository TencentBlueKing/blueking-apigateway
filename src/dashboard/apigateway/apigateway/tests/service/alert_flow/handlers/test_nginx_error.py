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

from apigateway.service.alert_flow.handlers import nginx_error


class TestNginxErrorAlerter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.alerter = nginx_error.NginxErrorAlerter(notice_ways=[])

    def test_get_receivers(self, settings, mock_event):
        settings.APIGW_MANAGERS = ["admin"]

        result = self.alerter.get_receivers(mock_event)
        assert result == ["admin"]

    def test_get_message(self, mock_event):
        mock_event.extend = {
            "log_records": [
                {
                    "_source": {
                        "log": "1990/09/16 10:28:41 [error] access forbidden by rule, server: bkapi.example.com",
                    }
                }
            ]
        }
        result = self.alerter.get_message(mock_event)
        assert result != ""
