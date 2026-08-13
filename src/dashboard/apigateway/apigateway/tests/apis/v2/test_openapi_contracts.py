# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
from pathlib import Path

from rest_framework import serializers, status

from apigateway.apis.v2.inner.views import AppRequestLogListApi, MCPServerAppPermissionRecordRetrieveApi
from apigateway.apis.v2.open.views import GatewayReleasedResourceListApi, MCPServerAppPermissionRecordListApi
from apigateway.apis.v2.sync.serializers import SDKGenerateInputSLZ
from apigateway.apis.v2.sync.views import (
    DocImportByArchiveApi,
    ResourceVersionListCreateApi,
    ResourceVersionReleaseApi,
    SDKGenerateApi,
)
from apigateway.utils.yaml import yaml_loads

RESOURCE_DEFINITION_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "apigw-definitions" / "bk-apigateway-resources.yaml"
)


def test_sync_api_response_status_schema_matches_runtime():
    assert set(DocImportByArchiveApi.post._swagger_auto_schema["responses"]) == {status.HTTP_201_CREATED}
    assert set(ResourceVersionListCreateApi.get._swagger_auto_schema["responses"]) == {status.HTTP_200_OK}
    assert set(ResourceVersionReleaseApi.post._swagger_auto_schema["responses"]) == {status.HTTP_200_OK}


def test_sdk_generate_schema_matches_runtime_payload():
    schema = SDKGenerateApi.post._swagger_auto_schema

    assert isinstance(schema["request_body"], SDKGenerateInputSLZ)
    response = schema["responses"][status.HTTP_201_CREATED]
    assert isinstance(response, serializers.ListSerializer)


def test_open_permission_apply_record_list_response_is_array():
    response = MCPServerAppPermissionRecordListApi.get._swagger_auto_schema["responses"][status.HTTP_200_OK]

    assert isinstance(response, serializers.ListSerializer)


def test_released_resource_list_schema_is_paginated_count_results_object():
    response = GatewayReleasedResourceListApi.get._swagger_auto_schema["responses"][status.HTTP_200_OK]

    assert GatewayReleasedResourceListApi.pagination_class is not None
    assert isinstance(response, serializers.Serializer)
    assert not isinstance(response, serializers.ListSerializer)
    assert set(response.fields) == {"count", "results"}


def test_inner_permission_apply_record_retrieve_response_is_object():
    response = MCPServerAppPermissionRecordRetrieveApi.get._swagger_auto_schema["responses"][status.HTTP_200_OK]

    assert isinstance(response, serializers.Serializer)
    assert not isinstance(response, serializers.ListSerializer)
    assert isinstance(response.fields["mcp_server"].fields["tools_count"], serializers.IntegerField)
    assert isinstance(response.fields["record"].fields["handled_by"], serializers.SerializerMethodField)
    handled_by_schema = response.fields["record"].get_handled_by._swagger_serializer
    assert isinstance(handled_by_schema, serializers.ListField)


def test_request_log_response_schema_uses_standard_paginated_object():
    response = AppRequestLogListApi.get._swagger_auto_schema["responses"][status.HTTP_200_OK]

    assert isinstance(response, serializers.Serializer)
    assert not isinstance(response, serializers.ListSerializer)
    assert set(response.fields) == {"count", "results"}


def test_registered_resource_schemas_match_runtime_contracts():
    paths = yaml_loads(RESOURCE_DEFINITION_PATH.read_text())["paths"]

    sdk_operation = paths["/api/v2/sync/gateways/{gateway_name}/sdks/"]["post"]
    assert set(sdk_operation["responses"]) == {"201"}
    sdk_data_schema = sdk_operation["responses"]["201"]["content"]["application/json"]["schema"]["properties"]["data"]
    assert sdk_data_schema["type"] == "array"

    retrieve_operation = paths["/api/v2/inner/mcp-server/permissions/apply-records/{record_id}/"]["get"]
    assert {parameter["name"] for parameter in retrieve_operation["parameters"]} == {
        "record_id",
        "target_app_code",
    }
    retrieve_data_schema = retrieve_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "properties"
    ]["data"]
    assert retrieve_data_schema["type"] == "object"
    assert set(retrieve_data_schema["properties"]) == {"mcp_server", "record"}
    assert retrieve_data_schema["properties"]["mcp_server"]["properties"]["tools_count"]["type"] == "integer"
    assert retrieve_data_schema["properties"]["record"]["properties"]["handled_by"]["type"] == "array"


def test_registered_v2_list_responses_use_standard_pagination_contract():
    paths = yaml_loads(RESOURCE_DEFINITION_PATH.read_text())["paths"]
    released_resources_operation = paths[
        "/api/v2/open/gateways/{gateway_name}/released/stages/{stage_name}/resources/"
    ]["get"]
    operations = [
        paths["/api/v2/sync/gateways/{gateway_name}/resource_versions/"]["get"],
        paths["/api/v2/open/mcp-servers/permissions/apply-records/"]["get"],
        released_resources_operation,
        paths["/api/v2/inner/apps/{app_code}/monitor/request-logs/"]["get"],
    ]

    for operation in operations:
        data_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["data"]
        assert data_schema["type"] == "object"
        assert set(data_schema["properties"]) == {"count", "results"}
        assert data_schema["properties"]["results"]["type"] == "array"

    query_parameter_names = {
        parameter["name"] for parameter in released_resources_operation["parameters"] if parameter["in"] == "query"
    }
    assert query_parameter_names == {"limit", "offset"}
