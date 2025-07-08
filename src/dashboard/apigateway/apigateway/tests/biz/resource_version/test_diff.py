# -*- coding: utf-8
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
import json
from typing import Dict, List, Optional, Text, Tuple, Union
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from apigateway.biz.resource_version import (
    DiffMixin,
    ResourceContexts,
    ResourceDifferHandler,
    ResourceHTTPProxy,
    ResourceMockProxy,
    ResourcePluginConfig,
)


class Group(BaseModel, DiffMixin):
    name: Text


class User(BaseModel, DiffMixin):
    id: int
    name: Text
    group: Group

    def diff_group(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.group.diff(target.group)


class TestDiffMixin:
    @pytest.mark.parametrize(
        "source, target, expected",
        [
            # equal
            (
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                {"source": {}, "target": {}},
            ),
            # id not equal
            (
                {"id": 2, "name": "t1", "group": {"name": "t"}},
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                {"source": {"id": 2}, "target": {"id": 1}},
            ),
            # id/name not equal
            (
                {"id": 2, "name": "t2", "group": {"name": "t"}},
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                {
                    "source": {"id": 2, "name": "t2"},
                    "target": {"id": 1, "name": "t1"},
                },
            ),
            # name/group not equal
            (
                {"id": 1, "name": "t2", "group": {"name": "g2"}},
                {"id": 1, "name": "t1", "group": {"name": "g1"}},
                {
                    "source": {"name": "t2", "group": {"name": "g2"}},
                    "target": {"name": "t1", "group": {"name": "g1"}},
                },
            ),
        ],
    )
    def test_diff(self, source, target, expected):
        source = User.model_validate(source)
        target = User.model_validate(target)
        source_diff, target_diff = source.diff(target)

        assert source_diff == expected["source"]
        assert target_diff == expected["target"]

    @pytest.mark.parametrize(
        "source, target, key, expected",
        [
            (
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                "id",
                {"source": None, "target": None},
            ),
            (
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                {"id": 1, "name": "t2", "group": {"name": "t"}},
                "name",
                {"source": "t1", "target": "t2"},
            ),
            (
                {"id": 2, "name": "t1", "group": {"name": "t"}},
                {"id": 1, "name": "t1", "group": {"name": "t"}},
                "group",
                {"source": None, "target": None},
            ),
            # id/name not equal
            (
                {"id": 2, "name": "t2", "group": {"name": "t1"}},
                {"id": 1, "name": "t1", "group": {"name": "t2"}},
                "group",
                {
                    "source": {"name": "t1"},
                    "target": {"name": "t2"},
                },
            ),
        ],
    )
    def test_diff_with_field_value(self, source, target, key, expected):
        source = User.model_validate(source)
        target = User.model_validate(target)
        source_diff, target_diff = source._diff_with_field_value(target, key)

        assert source_diff == expected["source"]
        assert target_diff == expected["target"]


class TestResourceProxyDiffer:
    @pytest.mark.parametrize(
        "source_proxy, target_proxy, expected",
        [
            # http
            (
                {
                    "type": "http",
                    "config": json.dumps(
                        {
                            "method": "GET",
                            "path": "/",
                            "timeout": 10,
                            "upstreams": {},
                            "transform_headers": {},
                        }
                    ),
                },
                {
                    "type": "http",
                    "config": json.dumps(
                        {
                            "method": "POST",
                            "path": "/echo",
                            "timeout": 20,
                            "upstreams": {},
                            "transform_headers": {},
                        }
                    ),
                },
                (
                    {"config": {"method": "GET", "path": "/", "timeout": 10}},
                    {"config": {"method": "POST", "path": "/echo", "timeout": 20}},
                ),
            ),
            # mock
            (
                {
                    "type": "mock",
                    "config": json.dumps(
                        {
                            "code": 200,
                            "body": "",
                            "headers": {},
                        }
                    ),
                },
                {
                    "type": "mock",
                    "config": json.dumps(
                        {
                            "code": 301,
                            "body": "t",
                            "headers": {},
                        }
                    ),
                },
                (
                    {"config": {"code": 200, "body": ""}},
                    {"config": {"code": 301, "body": "t"}},
                ),
            ),
            # http && mock
            (
                {
                    "type": "http",
                    "config": json.dumps(
                        {
                            "method": "GET",
                            "path": "/",
                            "timeout": 10,
                            "upstreams": {},
                            "transform_headers": {},
                        }
                    ),
                },
                {
                    "type": "mock",
                    "config": json.dumps(
                        {
                            "code": 301,
                            "body": "t",
                            "headers": {},
                        }
                    ),
                },
                (
                    {
                        "type": "http",
                        "backend_id": 0,
                        "config": {
                            "method": "GET",
                            "path": "/",
                            "match_subpath": False,
                            "timeout": 10,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    {
                        "type": "mock",
                        "config": {
                            "code": 301,
                            "body": "t",
                            "headers": {},
                        },
                    },
                ),
            ),
        ],
    )
    def test_diff_proxy(self, source_proxy, target_proxy, expected):
        class ResourceProxyDiffer(ResourceDifferHandler):
            id: int = 0
            name: Text = ""
            description: Text = ""
            method: Text = ""
            path: Text = ""
            contexts: ResourceContexts = None
            disabled_stages: List[Text] = []
            plugins: List[ResourcePluginConfig] = []
            doc_updated_time: Dict[str, str] = {}

        source_differ = ResourceProxyDiffer(proxy=source_proxy)
        target_differ = ResourceProxyDiffer(proxy=target_proxy)
        result = source_differ.diff_proxy(target_differ)
        assert result == expected

    class TestResourcePluginDiffer:
        @pytest.mark.parametrize(
            "source_plugins, target_plugins, expected",
            [
                (
                    [
                        {
                            "id": 1,
                            "name": "bk-mock",
                            "type": "2",
                            "config": {
                                "response_status": 200,
                                "response_example": "success",
                                "response_headers": "application/text",
                            },
                        }
                    ],
                    [
                        {
                            "id": 1,
                            "name": "bk-mock",
                            "type": "2",
                            "config": {
                                "response_status": 200,
                                "response_example": "fail",
                                "response_headers": "application/text",
                            },
                        }
                    ],
                    (
                        {
                            "2": {
                                "id": 1,
                                "name": "bk-mock",
                                "type": "2",
                                "config": {
                                    "response_status": 200,
                                    "response_example": "success",
                                    "response_headers": "application/text",
                                },
                            }
                        },
                        {
                            "2": {
                                "id": 1,
                                "name": "bk-mock",
                                "type": "2",
                                "config": {
                                    "response_status": 200,
                                    "response_example": "fail",
                                    "response_headers": "application/text",
                                },
                            }
                        },
                    ),
                ),
                (
                    [
                        {
                            "id": 1,
                            "name": "bk-mock",
                            "type": "2",
                            "config": {
                                "response_status": 200,
                                "response_example": "success",
                                "response_headers": "application/text",
                            },
                        }
                    ],
                    [
                        {
                            "id": 1,
                            "name": "bk-mock",
                            "type": "2",
                            "config": {
                                "response_status": 200,
                                "response_example": "success",
                                "response_headers": "application/text",
                            },
                        }
                    ],
                    ([{}, {}]),
                ),
            ],
        )
        def test_diff_plugin(self, source_plugins, target_plugins, expected):
            class ResourceProxyDiffer(ResourceDifferHandler):
                id: int = 0
                name: Text = ""
                description: Text = ""
                method: Text = ""
                path: Text = ""
                contexts: ResourceContexts = None
                proxy: Union[ResourceHTTPProxy, ResourceMockProxy] = None
                disabled_stages: List[Text] = []
                doc_updated_time: Dict[str, str] = {}

            source_differ = ResourceProxyDiffer(plugins=source_plugins)
            target_differ = ResourceProxyDiffer(plugins=target_plugins)
            result = source_differ.diff_plugins(target_differ)
            assert json.dumps(result) == json.dumps(expected)


class ResourceProxyHTTPConfig:
    @pytest.mark.parametrize(
        "source, target, expected",
        [
            # empty and equal
            ({"transform_headers": {}}, {"transform_headers": {}}, (None, None)),
            # not empty and equal
            (
                {"transform_headers": {"set": {"X-Token": "t"}}},
                {"transform_headers": {"set": {"X-Token": "t"}}},
                (None, None),
            ),
            # not equal
            (
                {"transform_headers": {"set": {"X-Token": "t"}}},
                {"transform_headers": {}},
                (
                    {"transform_headers": {"set": {"X-Token": "t"}}},
                    {"transform_headers": {}},
                ),
            ),
            # has not exist field
            (
                {
                    "transform_headers": {
                        "set": {"X-Token": "t"},
                        "delete": ["X-Token"],
                        "add": {"X-Token": "t"},
                    }
                },
                {"transform_headers": {"set": {"X-Token": "t"}}},
                (
                    {"transform_headers": {"set": {"X-Token": "t"}, "delete": ["X-Token"]}},
                    {"transform_headers": {"set": {"X-Token": "t"}}},
                ),
            ),
        ],
    )
    def test_clean_transform_headers(self, source, target, expected):
        config = {
            "method": "GET",
            "path": "/",
            "match_subpath": False,
            "timeout": 30,
        }
        source.update(config)
        target.update(config)

        source_differ = ResourceProxyHTTPConfig(**source)
        target_differ = ResourceProxyHTTPConfig(**target)
        result = source_differ.diff(target_differ)
        assert result == expected


class TestResourceDifferHandler:
    @patch("apigateway.biz.resource_version.ResourceDifferHandler.model_validate")
    def test_diff_resource_version_data(self, mock_parse_obj):
        class ResourceDifferMock(BaseModel, DiffMixin):
            id: int
            name: str
            method: str
            path: str

        mock_parse_obj.side_effect = lambda x: ResourceDifferMock.model_validate(x)

        source_data = [
            {
                "id": 1,
                "name": "n1",
                "method": "GET",
                "path": "/p1",
            },
            {
                "id": 3,
                "name": "n3",
                "method": "POST",
                "path": "/p3",
            },
        ]
        target_data = [
            {
                "id": 2,
                "name": "n2",
                "method": "POST",
                "path": "/p2",
            },
            {
                "id": 3,
                "name": "nn",
                "method": "GET",
                "path": "/p3",
            },
        ]

        result = ResourceDifferHandler.diff_resource_version_data(source_data, target_data, {}, {})

        assert result == {
            "add": [{"id": 2, "name": "n2", "method": "POST", "path": "/p2"}],
            "delete": [{"id": 1, "name": "n1", "method": "GET", "path": "/p1"}],
            "update": [
                {
                    "source": {
                        "id": 3,
                        "name": "n3",
                        "method": "POST",
                        "path": "/p3",
                        "diff": {"name": "n3", "method": "POST"},
                    },
                    "target": {
                        "id": 3,
                        "name": "nn",
                        "method": "GET",
                        "path": "/p3",
                        "diff": {"name": "nn", "method": "GET"},
                    },
                }
            ],
        }
