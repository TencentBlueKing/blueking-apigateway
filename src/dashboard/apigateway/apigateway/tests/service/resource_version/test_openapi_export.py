#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
#
import json
from copy import deepcopy

import pytest

from apigateway.service.resource_version import OpenAPIExportManager


@pytest.mark.parametrize("version", [None, "OpenAPIV2.0", "OpenAPIV3.0", "OpenAPIV3.1"])
def test_openapi_content_matches_serialized_export(version):
    resources = [
        {
            "name": "get_users",
            "description": "用户列表",
            "method": "GET",
            "path": "/users",
            "openapi_schema": {"parameters": [{"name": "name", "in": "query", "schema": {"type": "string"}}]},
        }
    ]
    if version:
        resources[0]["openapi_schema"]["version"] = version
    manager = OpenAPIExportManager(include_bk_apigateway_resource=False)
    content = manager.get_openapi_content(deepcopy(resources))
    serialized = manager.export_openapi(deepcopy(resources), file_type="json")
    assert content == json.loads(serialized)
    assert content["paths"]["/users"]["get"]["responses"] == {"default": {"description": ""}}
    assert content["openapi"] == ("3.1.0" if version == "OpenAPIV3.1" else "3.0.1")
