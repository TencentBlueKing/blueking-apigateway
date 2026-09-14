#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
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
import copy
import json
from types import SimpleNamespace

import pytest
from openapi_spec_validator.versions import OPENAPIV31

from apigateway.service.resource_version.openapi_export import OpenAPIExportManager


def test_get_openapi_content_returns_oas3_without_mutating_resources(fake_resource_dict):
    resources = [
        {
            **fake_resource_dict,
            "openapi_schema": {
                "version": str(OPENAPIV31),
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer", "format": "int64"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            },
        }
    ]
    original = copy.deepcopy(resources)

    document = OpenAPIExportManager(
        include_bk_apigateway_resource=False,
        title=resources[0]["name"],
    ).get_openapi_content(resources)

    operation = document["paths"][resources[0]["path"]][resources[0]["method"].lower()]
    assert document["openapi"] == "3.1.0"
    assert operation["operationId"] == resources[0]["name"]
    assert operation["parameters"][0]["schema"]["format"] == "int64"
    assert "x-bk-apigateway-resource" not in operation
    assert resources == original


@pytest.mark.parametrize("include_extensions", [False, True])
def test_get_resource_version_openapi_returns_structured_document_without_mutating_snapshot(
    mocker, include_extensions
):
    resource = {
        "id": 1,
        "name": "get_users",
        "description": "Get users",
        "path": "/users/",
        "method": "GET",
        "is_public": True,
        "allow_apply_permission": True,
        "contexts": {"resource_auth": {"config": "{}"}},
        "proxy": {"backend_id": 2, "config": json.dumps({"method": "GET", "path": "/users/"})},
        "plugins": [],
    }
    original = copy.deepcopy(resource)
    resource_version = SimpleNamespace(
        id=3,
        version="1.2.3",
        gateway=SimpleNamespace(id=4, name="demo"),
        data=[resource],
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_backend_id_to_instance",
        return_value={2: SimpleNamespace(name="backend")},
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_gateway_resource_id_to_labels",
        return_value={1: [{"name": "users"}]},
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_resource_id_to_schema_by_resource_version",
        return_value={1: {"version": "3.0.1", "responses": {"200": {"description": "OK"}}}},
    )

    document = OpenAPIExportManager(include_bk_apigateway_resource=include_extensions).get_resource_version_openapi(
        resource_version
    )

    assert isinstance(document, dict)
    assert document["openapi"] == "3.0.1"
    assert document["paths"]["/users/"]["get"]["tags"] == ["users"]
    operation = document["paths"]["/users/"]["get"]
    if include_extensions:
        assert operation["x-bk-apigateway-resource"]["backend"]["name"] == "backend"
    else:
        assert "x-bk-apigateway-resource" not in operation
    assert resource == original
