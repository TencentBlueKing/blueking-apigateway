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

from apigateway.utils import header


@pytest.mark.parametrize(
    "key, expected",
    [
        ("X-Token", "X-Token"),
        ("x-token", "X-Token"),
        ("token", "Token"),
        ("X-Token-123", "X-Token-123"),
        ("x-tokeN", "X-Token"),
        ("x-123a", "X-123a"),
    ],
)
def test_canonical_header_key(key, expected):
    result = header.canonical_header_key(key)
    assert result == expected
