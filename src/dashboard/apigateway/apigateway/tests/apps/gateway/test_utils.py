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

from apigateway.apps.gateway.utils import get_gateway_feature_flags
from apigateway.core.constants import APIHostingTypeEnum


@pytest.mark.parametrize(
    "hosting_type, expected",
    [
        (
            APIHostingTypeEnum.DEFAULT,
            {
                "MICRO_GATEWAY_ENABLED": False,
                "PLUGIN_ENABLED": False,
            },
        ),
        (
            APIHostingTypeEnum.MICRO,
            {
                "MICRO_GATEWAY_ENABLED": True,
                "PLUGIN_ENABLED": True,
            },
        ),
    ],
)
def test_get_gateway_feature_flags(settings, hosting_type, expected):
    settings.GLOBAL_GATEWAY_FEATURE_FLAG = {
        "MICRO_GATEWAY_ENABLED": True,
        "PLUGIN_ENABLED": True,
    }
    result = get_gateway_feature_flags(hosting_type)
    for key, expected_flag in expected.items():
        assert result[key] == expected_flag
