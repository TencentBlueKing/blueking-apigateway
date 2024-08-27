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
from typing import Any, Dict, Hashable, Iterator, List, Mapping, Optional, Tuple

from jsonschema.validators import Draft4Validator, Draft202012Validator
from jsonschema_path import SchemaPath
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
from openapi_spec_validator.validation.exceptions import DuplicateOperationIDError
from openapi_spec_validator.validation.keywords import OperationValidator
from openapi_spec_validator.versions.datatypes import SpecVersion
from prance import ValidationError

openapi_validator_mapping: Mapping[SpecVersion, SpecValidatorProxy] = {
    versions.OPENAPIV2: openapi_v2_spec_validator,
    versions.OPENAPIV30: openapi_v30_spec_validator,
    versions.OPENAPIV31: openapi_v31_spec_validator,
}


class ApigwOperationValidator(OperationValidator):
    """
    重写openapi_spec_validator的OperationValidator,不需要校验路径参数
    """

    def __call__(
        self,
        url: str,
        name: str,
        operation: SchemaPath,
        path_parameters: Optional[SchemaPath],
    ) -> Iterator[ValidationError]:
        assert self.operation_ids_registry is not None

        operation_id = operation.getkey("operationId")
        if operation_id is not None and operation_id in self.operation_ids_registry:
            yield DuplicateOperationIDError(f"Operation ID '{operation_id}' for '{name}' in '{url}' is not unique")
        self.operation_ids_registry.append(operation_id)

        if "responses" in operation:
            responses = operation / "responses"
            yield from self.responses_validator(responses)

        if "parameters" in operation:
            parameters = operation / "parameters"
            yield from self.parameters_validator(parameters)

        return


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


def init_validator_schema():
    """
    初始化为schema_validator使用自定义schema
    """
    for spec_version in openapi_validator_mapping:
        get_apigw_schema_content = Proxy(partial(_get_apigw_schema_content, spec_version))
        # 修改一下spec_validator的 schema_validator
        if spec_version == versions.OPENAPIV31:
            SPEC2VALIDATOR[spec_version].schema_validator = Proxy(
                partial(Draft202012Validator, get_apigw_schema_content)
            )
        else:
            SPEC2VALIDATOR[spec_version].schema_validator = Proxy(partial(Draft4Validator, get_apigw_schema_content))
        SPEC2VALIDATOR[spec_version].keyword_validators["operation"] = ApigwOperationValidator


def convert_openapi2_formdata_to_openapi(
    formdata_params: List[Dict[str, Any]], consumers: List[str]
) -> Dict[str, Any]:
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
                content_type: {"schema": schema},
            }
        }

    return openapi_request_body


def convert_openapi2_parameters_to_openapi(parameters):
    """
    将 openapi parameters 转成openapi
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


def convert_openapi2_response_headers_to_openapi(headers: dict) -> dict:
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


def convert_parameters_to_openapi2(openapi_parameters):
    """
    转换 OpenAPI 3.0 的参数列表到 OpenAPI 2.0 的格式。
    """
    parameters_openapi2 = []
    for param in openapi_parameters:
        v2_param = param.copy()  # 复制参数对象
        if "schema" in param:
            # OpenAPI 3.0 中的 'schema' 需要被展开到参数对象的根级别
            v2_param.update(param["schema"])
            del v2_param["schema"]
        if "content" in param:
            # 对于参数的 'content'，我们只能选择一个媒体类型
            content_type, content_value = next(iter(param["content"].items()))
            v2_param["type"] = content_value["schema"]["type"]
            del v2_param["content"]
        parameters_openapi2.append(v2_param)
    return parameters_openapi2


def convert_request_body_to_openapi2(request_body):
    """
    转换 OpenAPI 3.0 的请求体到 OpenAPI 2.0 的参数格式。
    """
    parameters = []
    for content_type, content_value in request_body["content"].items():
        param = {
            "in": "body",
            "name": "body",
            "required": request_body.get("required", False),
            "schema": content_value["schema"],
            "consumes": [content_type],
        }
        # 添加对应媒体类型的 'consumes' 字段
        parameters.append(param)
    return parameters


def convert_responses_to_openapi2(responses):
    """
    转换 OpenAPI 3.0 的响应对象到 OpenAPI 2.0 的格式。
    """
    responses_openapi2 = {}
    for status_code, response3 in responses.items():
        response2 = {"description": response3.get("description", ""), "schema": {}}
        # OpenAPI 2.0 不支持每个响应状态码的多媒体类型，因此我们合并所有媒体类型
        for content_value in response3.get("content", {}).values():
            response2["schema"] = content_value["schema"]  # 直接取 schema，不区分媒体类型
        responses_openapi2[status_code] = response2
    return responses_openapi2


def convert_operation_v3_to_v2(v3_operation):
    """
    将 OpenAPI 3.0 的 operation 对象转换为 OpenAPI 2.0 的 operation 对象。
    :param v3_operation: OpenAPI 3.0 的 operation 对象
    :return: OpenAPI 2.0 的 operation 对象
    """
    v2_operation = {}

    # 复制基本信息，如描述、摘要、操作ID等
    for key in ["description", "summary", "operationId", "tags"]:
        if key in v3_operation:
            v2_operation[key] = v3_operation[key]

    # 转换 requestBody 并获取 consumes 列表
    if "requestBody" in v3_operation:
        parameters_body2, consumes = convert_request_body(v3_operation["requestBody"])
        v2_operation["parameters"] = parameters_body2
        v2_operation["consumes"] = consumes

    # 转换 parameters 并合并 requestBody 参数
    if "parameters" in v3_operation:
        parameters2 = convert_parameters(v3_operation["parameters"], v2_operation.get("consumes", []))
        v2_operation["parameters"] = v2_operation.get("parameters", []) + parameters2

    # 转换 responses 并获取 produces 列表
    if "responses" in v3_operation:
        responses2, produces = convert_responses(v3_operation["responses"])
        v2_operation["responses"] = responses2
        v2_operation["produces"] = produces

    return v2_operation


def convert_parameters(v3_parameters, consumes):
    """
    转换 OpenAPI 3.0 的参数列表到 OpenAPI 2.0 的格式。
    :param v3_parameters: OpenAPI 3.0 的参数列表
    :param consumes: 从 requestBody 提取的 consumes 列表
    :return: OpenAPI 2.0 的参数列表
    """
    v2_parameters = []
    for param in v3_parameters:
        v2_param = param.copy()  # 复制参数对象
        if "schema" in param:
            # OpenAPI 3.0 中的 'schema' 需要被展开到参数对象的根级别
            v2_param.update(param["schema"])
            del v2_param["schema"]
        if "content" in param:
            # 对于参数的 'content'，我们只能选择一个媒体类型
            content_type, content_value = next(iter(param["content"].items()))
            v2_param["type"] = content_value["schema"]["type"]
            # 如果参数的媒体类型在 consumes 中，添加到 'consumes' 字段
            if content_type in consumes:
                v2_param["consumes"] = [content_type]
            del v2_param["content"]
        v2_parameters.append(v2_param)
    return v2_parameters


def convert_request_body(v3_request_body):
    """
    转换 OpenAPI 3.0 的请求体到 OpenAPI 2.0 的参数格式。
    :param v3_request_body: OpenAPI 3.0 的请求体对象
    :return: OpenAPI 2.0 的参数列表和 consumes 列表
    """
    v2_parameters = []
    consumes = []
    for content_type, content_value in v3_request_body["content"].items():
        param2 = {
            "in": "body",
            "name": "body",  # OpenAPI 2.0 中请求体的名称通常是 'body'
            "required": v3_request_body.get("required", False),
            "schema": content_value["schema"],
        }
        v2_parameters.append(param2)
        consumes.append(content_type)
    return v2_parameters, consumes


def convert_responses(v3_responses):
    """
    转换 OpenAPI 3.0 的响应对象到 OpenAPI 2.0 的格式。
    :param v3_responses: OpenAPI 3.0 的响应对象
    :return: OpenAPI 2.0 的响应对象和 produces 列表
    """
    v2_responses = {}
    produces = []
    for status_code, response3 in v3_responses.items():
        response2 = {"description": response3.get("description", "")}
        # OpenAPI 2.0 不支持每个响应状态码的多媒体类型，因此我们合并所有媒体类型
        for content_type, content_value in response3.get("content", {}).items():
            response2["schema"] = content_value["schema"]
            produces.append(content_type)
        v2_responses[status_code] = response2
    return v2_responses, list(set(produces))  # 使用 set 去重


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

    def to_dict(self):
        """将对象转换为字典。"""
        return {"message": self.message, "json_path": self.json_path, "absolute_path": self.absolute_path}
