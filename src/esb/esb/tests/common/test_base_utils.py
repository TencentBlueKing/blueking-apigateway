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
import datetime
import json

import pytest

from common import base_utils


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {
                "datetime": datetime.datetime(2020, 1, 1, 12, 20, 30),
                "int": 12345,
                "str": "abc",
            },
            json.dumps(
                {
                    "datetime": "2020-01-01 12:20:30",
                    "int": 12345,
                    "str": "abc",
                }
            ),
        )
    ],
)
def test_jsonize(data, expected):
    result = base_utils.jsonize(data)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1", True),
        ("0", False),
        ("true", True),
        ("false", False),
        ("True", True),
        ("False", False),
        ("", False),
        (" ", False),
        (b"1", True),
        (b"0", False),
        (b"true", True),
        (b"false", False),
        (b"True", True),
        (b"False", False),
        (1, True),
        (0, False),
        (True, True),
        (False, False),
    ],
)
def test_str_bool(value, expected):
    result = base_utils.str_bool(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("RequestFriendHandler", "request_friend_handler"),
    ],
)
def test_smart_lower(value, expected):
    result = base_utils.smart_lower(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("request_friend_handler", "requestFriendHandler"),
    ],
)
def test_smart_upper(value, expected):
    result = base_utils.smart_upper(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("a", b"a"),
        (b"a", b"a"),
        (u"a", b"a"),
    ],
)
def test_smart_str(value, expected):
    result = base_utils.smart_str(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("a", "a"),
        (b"a", "a"),
        (u"a", "a"),
    ],
)
def test_smart_unicode(value, expected):
    result = base_utils.smart_unicode(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("a", "a"),
        (b"a", "a"),
        (u"a", "a"),
    ],
)
def test_smart_unicode_v2(value, expected):
    result = base_utils.smart_unicode_v2(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (["a", "b"], ["a", "b"]),
        (["a", "b", "a"], ["a", "b"]),
    ],
)
def test_unique(value, expected):
    result = base_utils.unique(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            {
                "a": None,
                "b": "",
                "c": [],
                "d": {},
            },
            {},
        ),
        (
            {
                "a": 1,
                "b": "x",
            },
            {
                "a": 1,
                "b": "x",
            },
        ),
    ],
)
def test_get_not_empty_value(value, expected):
    result = base_utils.get_not_empty_value(value)
    assert result == expected


@pytest.mark.parametrize(
    "length",
    [
        30,
        10,
    ],
)
def test_generate_token(length):
    result = base_utils.generate_token(length)
    assert isinstance(result, str)
    assert len(result) == length


@pytest.mark.parametrize(
    "method, data, content_type, expected",
    [
        ("get", {"a": "b", "c": "d"}, None, {"a": "b", "c": "d"}),
        ("post", {"a": "b", "c": "d"}, None, {"a": "b", "c": "d"}),
        ("post", json.dumps({"a": "b", "c": "d"}), "application/json", {"a": "b", "c": "d"}),
        ("post", "a=b&c=d", "application/x-www-form-urlencoded", {"a": "b", "c": "d"}),
    ],
)
def test_get_request_params(request_factory, method, data, content_type, expected):
    kwargs = {
        "data": data,
    }
    if content_type:
        kwargs["content_type"] = content_type

    request = getattr(request_factory, method)("", **kwargs)
    result = base_utils.get_request_params(request)
    assert request.method == method.upper()
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (1620973760, "2021-05-14 06:29:20"),
        (datetime.datetime(2021, 5, 14, 14, 29, 16, tzinfo=datetime.timezone.utc), "2021-05-14 14:29:16"),
        (datetime.datetime(2021, 5, 14, 14, 29, 16, tzinfo=datetime.timezone.utc).date(), "2021-05-14"),
    ],
)
def test_datetime_format(value, expected):
    result = base_utils.datetime_format(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("abcd", "e2fc714c4727ee9395f324cd2e7f331f"),
    ],
)
def test_get_md5(value, expected):
    result = base_utils.get_md5(value)
    assert result == expected


@pytest.mark.parametrize("data, expected", [({"a": "b", "x": 1}, "a: b\nx: 1\n"), ({"a": "测试"}, "a: 测试\n")])
def test_yaml_dumps(data, expected):
    result = base_utils.yaml_dumps(data)
    assert result == expected


@pytest.mark.parametrize(
    "data, keys, default, expected",
    [
        (
            {"a": "b"},
            ["a"],
            None,
            "b",
        ),
        (
            {"a": "b", "c": "d"},
            ["a", "c"],
            None,
            "b",
        ),
        (
            {"a": "b", "c": "d"},
            ["not-exist", "c"],
            None,
            "d",
        ),
        (
            {"a": "", "c": "d"},
            ["a", "c"],
            None,
            "d",
        ),
        (
            {},
            ["a", "c"],
            "",
            "",
        ),
    ],
)
def test_get_first_not_empty_value(data, keys, default, expected):
    result = base_utils.get_first_not_empty_value(data, keys, default)
    assert result == expected


@pytest.mark.parametrize(
    "base_url, path, expected",
    [
        (None, "/test/", "/test/"),
        ("", "/test/", "/test/"),
        ("http://demo.example.com/", "/test/", "http://demo.example.com/test/"),
        ("http://demo.example.com/test", "/red/", "http://demo.example.com/test/red/"),
        ("http://demo.example.com/test", "", "http://demo.example.com/test"),
    ],
)
def test_urljoin(base_url, path, expected):
    result = base_utils.urljoin(base_url, path)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            "request_friend_handler",
            "RequestFriendHandler",
        ),
        (
            "request",
            "Request",
        ),
    ],
)
def test_smart_upper_v2(value, expected):
    result = base_utils.smart_upper_v2(value)
    assert result == expected
