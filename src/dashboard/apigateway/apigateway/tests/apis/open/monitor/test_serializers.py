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

from apigateway.apis.open.monitor import serializers


class TestMonitorCallbackSLZ:
    @pytest.mark.parametrize(
        "params, expected_is_valid",
        [
            (
                {},
                False,
            ),
            (
                {
                    "token": "",
                },
                False,
            ),
            (
                {
                    "token": "error",
                },
                False,
            ),
            (
                {
                    "token": "my-token",
                },
                True,
            ),
        ],
    )
    def test_validate(self, settings, params, expected_is_valid):
        settings.BKMONITOR_CALLBACK_TOKEN = "my-token"

        slz = serializers.MonitorCallbackSLZ(data=params)
        result = slz.is_valid(raise_exception=False)
        assert result == expected_is_valid
