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

from apigateway.utils.url import get_host


class TestURL:
    @pytest.mark.parametrize(
        "url, expected",
        [
            (
                "http://bking.test.com",
                "bking.test.com",
            ),
            (
                "https://bking.test.com:8080",
                "bking.test.com:8080",
            ),
            (
                "bking.test.com",
                "",
            ),
            (
                "abc",
                "",
            ),
        ],
    )
    def test_get_host(self, url, expected):
        assert expected == get_host(url)
