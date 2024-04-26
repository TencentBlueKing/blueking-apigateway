#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from functools import partial
from importlib.resources import as_file, files
from os import path
from typing import Any, Dict, Hashable, List, Mapping, Tuple

from jsonschema.validators import Draft4Validator, Draft202012Validator
from jsonschema_path.readers import FilePathReader
from lazy_object_proxy import Proxy
from openapi_spec_validator import versions
from openapi_spec_validator.shortcuts import SPEC2VALIDATOR
from openapi_spec_validator.validation import (
    SpecValidatorProxy,
    openapi_v2_spec_validator,
    openapi_v30_spec_validator,
    openapi_v31_spec_validator,
)
from openapi_spec_validator.versions.datatypes import SpecVersion

openapi_validator_mapping: Mapping[SpecVersion, SpecValidatorProxy] = {
    versions.OPENAPIV2: openapi_v2_spec_validator,
    versions.OPENAPIV30: openapi_v30_spec_validator,
    versions.OPENAPIV31: openapi_v31_spec_validator,
}


def _load_open_schema_for_apigw(version: str) -> Tuple[Mapping[Hashable, Any], str]:
    """
    根据不同版本加载不同版本的 schema
    """
    schema_path = f"schemas/openapi_{version}_schema.json"
    ref = files("apigateway.biz.resource.importer") / schema_path
    with as_file(ref) as resource_path:
        schema_path_full = path.join(path.dirname(__file__), resource_path)
    return FilePathReader(schema_path_full).read()


def _get_apigw_schema_content(spec_version: SpecVersion) -> Mapping[Hashable, Any]:
    """
    加载不同版本 schema 内容
    """
    content, _ = _load_open_schema_for_apigw(f"{spec_version.major}.{spec_version.minor}")
    return content


def get_apigw_schema_validator(spec_version: SpecVersion) -> SpecValidatorProxy:
    """
    根据版本获取不同的 spec_validator
    """
    spec_validator = SPEC2VALIDATOR[spec_version]

    get_apigw_schema_content = Proxy(partial(_get_apigw_schema_content, spec_version))

    # 修改一下spec_validator的 schema_validator
    if spec_version == versions.OPENAPIV31:
        spec_validator.schema_validator = Proxy(partial(Draft202012Validator, get_apigw_schema_content))
    else:
        spec_validator.schema_validator = Proxy(partial(Draft4Validator, get_apigw_schema_content))

    return openapi_validator_mapping[spec_version]


def set_openapi_parser_schema_validator(spec_version: SpecVersion):
    """
    设置openai转换器使用的schema_validator
    """
    get_apigw_schema_content = Proxy(partial(_get_apigw_schema_content, spec_version))

    SPEC2VALIDATOR[spec_version].schema_validator = Proxy(partial(Draft4Validator, get_apigw_schema_content))


def convert_swagger_formdata_to_openapi(formdata_params: List[Dict[str, Any]], consumers: List[str]) -> Dict[str, Any]:
    """
    将Swagger 2.0的formData参数转换为OpenAPI 3.0的requestBody。
    """

    # 初始化openapi_request_body的结构
    openapi_request_body = {}

    # 如果只有一个consumer且为application/json，则替换为multipart/form-data
    if len(consumers) == 1 and consumers[0] == "application/json":
        consumers[0] = "multipart/form-data"

    # 遍历每个consumer类型
    for content_type in consumers:
        properties = {}
        required = []

        # 遍历每个参数
        for param in formdata_params:
            prop_type = "string" if param["type"] == "file" else param.get("type", "string")
            prop = {"type": prop_type}
            # 处理其他可选属性
            for key in ["format", "items", "enum", "default"]:
                if key in param:
                    prop[key] = param[key]

            # 添加属性到properties字典
            properties[param["name"]] = prop

            # 处理必需字段
            if param.get("required", False):
                required.append(param["name"])

        # 构建content字典
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        openapi_request_body = {
            "content": {
                content_type: schema,
            }
        }

    return openapi_request_body


def convert_swagger_parameters_to_openapi(parameters):
    """
    将 swagger parameters 转成openapi
    """
    openapi_params = []
    for param in parameters:
        openapi_param = {
            "name": param.get("name"),
            "in": param.get("in"),
            "required": param.get("required", False),
            "description": param.get("description", ""),
            "schema": {},
        }

        # Swagger 2.0 'type' is moved to 'schema' in OpenAPI 3.0
        if "type" in param:
            openapi_param["schema"]["type"] = param["type"]

        # Swagger 2.0 'items' and 'collectionFormat' are moved inside 'schema' in OpenAPI 3.0
        if "items" in param:
            openapi_param["schema"]["items"] = param["items"]
        if "collectionFormat" in param:
            openapi_param["style"] = "form" if param["collectionFormat"] == "multi" else "simple"

        # Swagger 2.0 'format' is moved to 'schema' in OpenAPI 3.0
        if "format" in param:
            openapi_param["schema"]["format"] = param["format"]

        # Swagger 2.0 'enum' is moved to 'schema' in OpenAPI 3.0
        if "enum" in param:
            openapi_param["schema"]["enum"] = param["enum"]

        # Swagger 2.0 'default' is moved to 'schema' in OpenAPI 3.0
        if "default" in param:
            openapi_param["schema"]["default"] = param["default"]

        # Add other Swagger 2.0 to OpenAPI 3.0 conversions as needed

        openapi_params.append(openapi_param)

    return openapi_params


def convert_swagger_response_headers_to_openapi(headers: dict) -> dict:
    """
    将swagger2.0 response headers 转为openapi3.0
    """
    openapi_headers = {}
    for header_name, header_spec in headers.items():
        openapi_header = {
            "schema": {"type": header_spec.get("type")},
            "description": header_spec.get("description", ""),
        }

        # Swagger 2.0 'format' is moved to 'schema' in OpenAPI 3.0
        if "format" in header_spec:
            openapi_header["schema"]["format"] = header_spec["format"]

        # Swagger 2.0 'items' is moved to 'schema' in OpenAPI 3.0 for arrays
        if "items" in header_spec:
            openapi_header["schema"]["items"] = header_spec["items"]

        # Swagger 2.0 'enum' is moved to 'schema' in OpenAPI 3.0
        if "enum" in header_spec:
            openapi_header["schema"]["enum"] = header_spec["enum"]

        # Add other Swagger 2.0 to OpenAPI 3.0 conversions as needed

        openapi_headers[header_name] = openapi_header
    return openapi_headers


class SchemaValidateErr:
    """验证schema错误的类"""

    def __init__(self, message: str, json_path: str, absolute_path: List[str]):
        """初始化新的SchemaValidationError对象。

        参数:
            message (str): 错误描述。
            json_path (str): 指示错误位置的JSON路径表达式。
            absolute_path (List[str]): 错误的绝对路径列表。
        """
        self.message = message
        self.json_path = json_path
        self.absolute_path = absolute_path
