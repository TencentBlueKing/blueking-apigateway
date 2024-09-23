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

from apigateway.utils.dict import (
    deep_update,
    update_existing,
)


@pytest.mark.parametrize(
    "mapping, updating_mapping, expected_mapping, msg",
    [
        (
            {"key": {"inner_key": 0}},
            {"other_key": 1},
            {"key": {"inner_key": 0}, "other_key": 1},
            "extra keys are inserted",
        ),
        (
            {"key": {"inner_key": 0}, "other_key": 1},
            {"key": [1, 2, 3]},
            {"key": [1, 2, 3], "other_key": 1},
            "values that can not be merged are updated",
        ),
        (
            {"key": {"inner_key": 0}},
            {"key": {"other_key": 1}},
            {"key": {"inner_key": 0, "other_key": 1}},
            "values that have corresponding keys are merged",
        ),
        (
            {"key": {"inner_key": {"deep_key": 0}}},
            {"key": {"inner_key": {"other_deep_key": 1}}},
            {"key": {"inner_key": {"deep_key": 0, "other_deep_key": 1}}},
            "deeply nested values that have corresponding keys are merged",
        ),
    ],
)
def test_deep_update(mapping, updating_mapping, expected_mapping, msg):
    assert deep_update(mapping, updating_mapping) == expected_mapping, msg


def test_deep_update_is_not_mutating():
    mapping = {"key": {"inner_key": {"deep_key": 1}}}
    updated_mapping = deep_update(mapping, {"key": {"inner_key": {"other_deep_key": 1}}})
    assert updated_mapping == {"key": {"inner_key": {"deep_key": 1, "other_deep_key": 1}}}
    assert mapping == {"key": {"inner_key": {"deep_key": 1}}}


@pytest.mark.parametrize(
    "mapping, update, expected",
    [
        (
            {"key": 0},
            {"key": 1},
            {"key": 1},
        ),
        (
            {"key": 0, "other_key": 1},
            {"other_key": 2, "not_exist_key": 1},
            {"key": 0, "other_key": 2},
        ),
        (
            {"key": 0, "other_key": 1},
            {"not_exist_key": 1},
            {"key": 0, "other_key": 1},
        ),
    ],
)
def test_update_existing(mapping, update, expected):
    updated_mapping = update_existing(mapping, **update)
    assert updated_mapping == expected


def test_update_existing_is_not_mutating():
    mapping = {"key": {"inner_key": 1}}
    updated_mapping = update_existing(mapping, key=0)
    assert updated_mapping == {"key": 0}
    assert mapping == {"key": {"inner_key": 1}}
