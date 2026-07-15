#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

import pytest
from ddf import G

from apigateway.apps.openapi.models import OpenAPIResourceSchemaVersion
from apigateway.core.constants import ResourceKindEnum
from apigateway.core.models import ResourceVersion
from apigateway.service.resource_version import (
    get_resource_id_to_schema_by_resource_version,
    get_resource_names_set,
    get_resource_schema,
    get_used_stage_vars,
    make_resource_schema_version,
)


@pytest.fixture(autouse=True)
def clear_resource_version_schema_caches():
    get_resource_names_set.cache_clear()
    get_used_stage_vars.cache_clear()
    yield
    get_resource_names_set.cache_clear()
    get_used_stage_vars.cache_clear()


def test_get_resource_schema_returns_empty_without_schema(fake_resource_version):
    assert get_resource_schema(fake_resource_version.id, resource_id=1) == {}


def test_get_resource_schema_returns_matching_schema(fake_resource_version):
    G(
        OpenAPIResourceSchemaVersion,
        resource_version=fake_resource_version,
        schema=[
            {
                "resource_id": 1,
                "schema": {"parameters": [{"name": "foo"}]},
            },
            {
                "resource_id": 2,
                "schema": {"requestBody": {"content": {}}},
            },
        ],
    )

    assert get_resource_schema(fake_resource_version.id, resource_id=2) == {
        "requestBody": {"content": {}},
    }


def test_get_resource_id_to_schema_by_resource_version_returns_empty_without_schema(fake_resource_version):
    assert get_resource_id_to_schema_by_resource_version(fake_resource_version.id) == {}


def test_get_resource_id_to_schema_by_resource_version_returns_schema_map(fake_resource_version):
    G(
        OpenAPIResourceSchemaVersion,
        resource_version=fake_resource_version,
        schema=[
            {
                "resource_id": 1,
                "schema": {"parameters": [{"name": "foo"}]},
            },
            {
                "resource_id": 2,
                "schema": {"requestBody": {"content": {}}},
            },
        ],
    )

    assert get_resource_id_to_schema_by_resource_version(fake_resource_version.id) == {
        1: {"parameters": [{"name": "foo"}]},
        2: {"requestBody": {"content": {}}},
    }


def test_get_resource_names_set_returns_empty_without_resource_version():
    assert get_resource_names_set(resource_version_id=0) == set()


def test_get_resource_names_set_returns_names(fake_resource_version):
    assert get_resource_names_set(fake_resource_version.id) == {
        resource["name"] for resource in fake_resource_version.data
    }


def test_get_resource_names_set_filters_by_kind_and_treats_missing_kind_as_standard(fake_resource_version):
    fake_resource_version.data = [
        {"name": "legacy-resource"},
        {"name": "standard-resource", "kind": ResourceKindEnum.STANDARD.value},
        {"name": "ai-resource", "kind": ResourceKindEnum.AI.value},
    ]
    fake_resource_version.save()

    assert get_resource_names_set(
        fake_resource_version.id,
        resource_kind=ResourceKindEnum.STANDARD.value,
    ) == {"legacy-resource", "standard-resource"}


@pytest.mark.parametrize(
    "resource_data, expected",
    [
        (
            [
                {
                    "proxy": {
                        "type": "mock",
                    }
                }
            ],
            {
                "in_path": [],
                "in_host": [],
            },
        ),
        (
            [
                {
                    "proxy": {
                        "type": "http",
                        "config": json.dumps(
                            {
                                "path": "/hello/{env.region}/",
                                "upstreams": {
                                    "hosts": [
                                        {"host": "https://{env.domain}"},
                                    ]
                                },
                            }
                        ),
                    }
                }
            ],
            {
                "in_path": ["region"],
                "in_host": ["domain"],
            },
        ),
        (
            [
                {
                    "proxy": {
                        "type": "http",
                        "config": json.dumps(
                            {
                                "path": "/hello/{env.region}/",
                                "upstreams": {},
                            }
                        ),
                    }
                }
            ],
            {
                "in_path": ["region"],
                "in_host": [],
            },
        ),
    ],
)
def test_get_used_stage_vars_matches_resource_version_handler_cases(fake_gateway, resource_data, expected):
    resource_version = G(
        ResourceVersion,
        gateway=fake_gateway,
        _data=json.dumps(resource_data),
    )

    assert get_used_stage_vars(fake_gateway.id, resource_version.id) == expected


def test_get_used_stage_vars_returns_vars_from_resource_data(fake_gateway):
    resource_version = G(
        ResourceVersion,
        gateway=fake_gateway,
        _data=json.dumps(
            [
                {
                    "proxy": {
                        "type": "http",
                        "config": '{"path": "/users/{env.prefix}", "upstreams": {"hosts": [{"host": "{env.domain}"}]}}',
                    },
                },
                {
                    "proxy": {
                        "type": "http",
                        "config": "{}",
                    },
                    "stage_vars": {
                        "in_path": ["explicit_path"],
                        "in_host": ["explicit_host"],
                    },
                },
            ]
        ),
    )

    result = get_used_stage_vars(fake_gateway.id, resource_version.id)

    assert set(result["in_path"]) == {"prefix", "explicit_path"}
    assert set(result["in_host"]) == {"domain", "explicit_host"}


def test_get_used_stage_vars_skips_ai_resources(fake_gateway):
    resource_version = G(
        ResourceVersion,
        gateway=fake_gateway,
        _data=json.dumps(
            [
                {
                    "kind": ResourceKindEnum.AI.value,
                    "proxy": {
                        "type": "http",
                        "config": "{}",
                    },
                },
                {
                    "kind": ResourceKindEnum.STANDARD.value,
                    "proxy": {
                        "type": "http",
                        "config": '{"path": "/users/{env.prefix}", "upstreams": {}}',
                    },
                },
            ]
        ),
    )

    assert get_used_stage_vars(fake_gateway.id, resource_version.id) == {
        "in_path": ["prefix"],
        "in_host": [],
    }


def test_get_used_stage_vars_returns_none_for_missing_resource_version(fake_gateway):
    assert get_used_stage_vars(fake_gateway.id, 0) is None


def test_make_resource_schema_version(fake_resource_version, fake_resource_schema):
    make_resource_schema_version(fake_resource_version)

    assert OpenAPIResourceSchemaVersion.objects.filter(resource_version_id=fake_resource_version.id).exists()
