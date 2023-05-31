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

from common.errors import APIError
from esb.bkcore.constants import LegacyPermissionLevel


class TestLegacyPermissionLevel:
    @pytest.mark.parametrize(
        "new_value, expected",
        [
            (
                "unlimited",
                {
                    "value": 0,
                    "label": "无限制",
                },
            ),
            (
                "normal",
                {
                    "value": 1,
                    "label": "普通权限",
                },
            ),
        ],
    )
    def test_from_new(self, new_value, expected):
        legacy = LegacyPermissionLevel.from_new(new_value)

        assert legacy.value == expected["value"]
        assert legacy.label == expected["label"]

    @pytest.mark.parametrize(
        "legacy_value, expected",
        [
            (0, "unlimited"),
            (1, "normal"),
            (2, "sensitive"),
            (3, "special"),
        ],
    )
    def test_get_new(self, legacy_value, expected):
        new = LegacyPermissionLevel.get_new(legacy_value)

        assert new.value == expected

    def test_get_new_error(self):
        with pytest.raises(APIError):
            LegacyPermissionLevel.get_new(4)
