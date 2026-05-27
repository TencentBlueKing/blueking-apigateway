#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from ddf import G

from apigateway.apps.openapi.models import OpenAPIResourceSchemaVersion
from apigateway.service.resource_version_schema import (
    get_resource_id_to_schema_by_resource_version,
    get_resource_names_set,
    get_resource_schema,
)


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
