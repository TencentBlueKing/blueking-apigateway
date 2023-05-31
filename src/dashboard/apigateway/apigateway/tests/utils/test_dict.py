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
from collections import OrderedDict

import pytest

from apigateway.utils.dict import (
    deep_update,
    from_exist_keys,
    get_item_by_path,
    new_dict,
    set_item_by_path,
    update_existing,
)


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            # include exist
            {
                "data": {"a": 1, "b": 2, "c": 3},
                "include": ["a", "c", "d"],
            },
            {"a": 1, "c": 3},
        ),
        (
            # exclude exist
            {
                "data": {"a": 1, "b": 2, "c": 3},
                "exclude": ["a", "c", "d"],
            },
            {"b": 2},
        ),
        (
            # exclude_none is true
            {
                "data": {"a": None, "b": 2, "c": None},
                "exclude_none": True,
            },
            {"b": 2},
        ),
        (
            # include and exclude exist
            {
                "data": {"a": 1, "b": 2, "c": 3},
                "include": set(["a", "c"]),
                "exclude": set(["b", "d"]),
            },
            {"a": 1, "c": 3},
        ),
        (
            # include exist and exclude_none is true
            {
                "data": {"a": 1, "b": 2, "c": None},
                "include": set(["b"]),
                "exclude_none": True,
            },
            {"b": 2},
        ),
    ],
)
def test_new_dict(params, expected):
    result = new_dict(**params)
    assert result == expected


@pytest.mark.parametrize(
    "data, keys, expected",
    [
        (
            {
                "a": 1,
                "b": 2,
            },
            ["a"],
            {
                "a": 1,
            },
        ),
        (
            {
                "a": 1,
                "b": 2,
            },
            ["a", "c"],
            {
                "a": 1,
            },
        ),
        (
            {
                "a": 1,
                "b": 2,
            },
            ["c", "d"],
            {},
        ),
    ],
)
def test_from_exist_keys(data, keys, expected):
    result = from_exist_keys(data, keys)
    assert result == expected


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
    updated_mapping = update_existing(mapping, **{"key": 0})
    assert updated_mapping == {"key": 0}
    assert mapping == {"key": {"inner_key": 1}}


@pytest.mark.parametrize(
    "paths, expected",
    [
        (["key1"], True),
        (["no_exists"], None),
        (["key2", "inner_key1"], {"deep_key": 1}),
        (["key2", "inner_key1", "deep_key"], 1),
        (["key2", "inner_key2"], ["a", "b"]),
        (["key2", "inner_key2", 1], "b"),
    ],
)
def test_get_item_by_path(paths, expected):
    item = {
        "key1": True,
        "key2": {
            "inner_key1": {
                "deep_key": 1,
            },
            "inner_key2": ["a", "b"],
        },
    }

    assert get_item_by_path(item, paths) == expected


def test_get_item_by_path_exceptional():
    with pytest.raises(TypeError):
        get_item_by_path(1, ["x"])


@pytest.mark.parametrize(
    "paths, value",
    [
        (["key1"], False),
        (["no_exists"], 2),
        (["no_exists", "with_inner_key"], 3),
        (["key2", "inner_key1"], [2]),
        (["key2", "inner_key1", "deep_key"], 2),
        (["key2", "inner_key2"], None),
        (["key2", "inner_key2", 1], "c"),
    ],
)
def test_set_item_by_path(paths, value):
    item = {
        "key1": True,
        "key2": {
            "inner_key1": {
                "deep_key": 1,
            },
            "inner_key2": ["a", "b"],
        },
    }
    set_item_by_path(item, paths, value)
    assert get_item_by_path(item, paths) == value


@pytest.mark.parametrize(
    "paths, value, type_,missing_type",
    [
        (["key"], 1, dict, dict),
        (["key1", "key2"], 1, dict, dict),
        (["key"], 1, dict, OrderedDict),
        (["key1", "key2"], 1, dict, OrderedDict),
        (["key"], 1, OrderedDict, OrderedDict),
        (["key1", "key2"], 1, OrderedDict, OrderedDict),
        (["key"], 1, OrderedDict, dict),
        (["key1", "key2"], 1, OrderedDict, dict),
        (["key"], 1, dict, None),
        (["key1", "key2"], 1, dict, None),
        (["key"], 1, OrderedDict, None),
        (["key1", "key2"], 1, OrderedDict, None),
    ],
)
def test_set_item_by_path_with_missing_type(paths, value, type_, missing_type):
    item = type_()
    set_item_by_path(item, paths, value, missing_type=missing_type)
    assert get_item_by_path(item, paths) == value
