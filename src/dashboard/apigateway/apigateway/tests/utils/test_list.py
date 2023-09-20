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

from apigateway.utils.list import chunk_list, get_duplicate_items


@pytest.mark.parametrize(
    "lst, n, expected",
    [
        ([], 2, []),
        ([1], 2, [[1]]),
        ([1, 2], 2, [[1, 2]]),
        ([1, 2, 3], 2, [[1, 2], [3]]),
        ([1, 2, 3, 4], 2, [[1, 2], [3, 4]]),
    ],
)
def test_chunk_list(lst, n, expected):
    result = list(chunk_list(lst, n))
    assert result == expected


@pytest.mark.parametrize(
    "items, expected",
    [
        (
            ["foo", "bar", "foo"],
            ["foo"],
        ),
        (
            [1, 2, 3, 2],
            [2],
        ),
    ],
)
def test_get_duplicate_items(items, expected):
    result = get_duplicate_items(items)
    assert result == expected
