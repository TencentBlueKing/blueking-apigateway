# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from openapi_spec_validator.validation.exceptions import UnresolvableParameterError
from openapi_spec_validator.versions import OPENAPIV2, get_spec_version
from openapi_spec_validator.versions.exceptions import OpenAPIVersionNotFound
from prance import ResolvingParser
from prance.util.url import ResolutionError

from apigateway.apps.support.constants import OpenAPIFormatEnum
from apigateway.utils.yaml import yaml_loads

from .constants import OpenAPIVersionKeyEnum
from .parser import BaseParser, OpenAPIV3Parser, ResourceDataConvertor
from .schema import (
    SchemaValidateErr,
    init_validator_schema,
    openapi_validator_mapping,
)
from .validate import ResourceImportValidator

if TYPE_CHECKING:
    from apigateway.biz.resource import ResourceData
    from apigateway.core.models import Gateway

# 初始化openapi validator schema
init_validator_schema()


class OpenAPIImportManager:
    """
    资源配置导入manager
    """

    def __init__(self, gateway: Gateway, data: Dict[str, Any], need_delete_unspecified_resources=False):
        self.version = None
        self.data = data
        self.gateway = gateway
        self._raw_resource_list: List[Dict[str, Any]] = []
        self._resource_list: List["ResourceData"] = []
        self.parser = None
        self.need_delete_unspecified_resources = need_delete_unspecified_resources

    @classmethod
    def load_from_content(
        cls, gateway: Gateway, content: str, need_delete_unspecified_resources=False
    ) -> "OpenAPIImportManager":
        content_format = cls.guess_content_format(content)
        # 显式地为 loads_func 提供一个类型注解
        loads_func: Callable[[str], Dict[str, Any]] = yaml_loads

        if content_format == OpenAPIFormatEnum.JSON:
            loads_func = json.loads

        return cls(
            gateway=gateway,
            data=loads_func(content),
            need_delete_unspecified_resources=need_delete_unspecified_resources,
        )

    @classmethod
    def guess_content_format(cls, content: str) -> OpenAPIFormatEnum:
        # 内容以 "{" 开头，则为 json 串，否则为 yaml 串
        if content.strip().startswith("{"):
            return OpenAPIFormatEnum.JSON

        return OpenAPIFormatEnum.YAML

    def validate(self) -> List[SchemaValidateErr]:
        """
        进行校验
        """
        # 在所有解析操作之前校验 $ref，防止外部引用导致 SSRF / 文件读取
        try:
            self._validate_refs(self.data)
        except ValueError as err:
            return [SchemaValidateErr(str(err), "$", [])]

        try:
            # 先获取 openapi版本
            spec_version = get_spec_version(self.data)
        except OpenAPIVersionNotFound:
            return [self._get_version_err()]

        self.version = spec_version

        # 获取 openapi validator
        spec_validator = openapi_validator_mapping[spec_version]

        schema_validate_result = [
            SchemaValidateErr(
                err.message,
                err.json_path,
                list(err.absolute_path),
            )
            for err in spec_validator.cls(self.data).iter_errors()
            if not isinstance(err, UnresolvableParameterError)  # 需要排除路径参数校验
        ]

        if len(schema_validate_result) > 0:
            return schema_validate_result

        # 进行逻辑校验

        try:
            self.parse()
        except (ResolutionError, ValueError) as err:
            return [SchemaValidateErr(str(err), "$", [])]

        validator = ResourceImportValidator(
            gateway=self.gateway,
            resource_data_list=self._resource_list,
            need_delete_unspecified_resources=self.need_delete_unspecified_resources,
        )

        return validator.validate()

    def _get_version_err(self) -> SchemaValidateErr:
        """
        获取 openapi 版本校验失败的 SchemaValidateErr
        """
        openapi_type = OpenAPIVersionKeyEnum.OpenAPI.value
        openapi_type_key = self.data.get(OpenAPIVersionKeyEnum.OpenAPI.value, None)
        if not openapi_type_key:
            openapi_type_key = self.data.get(OpenAPIVersionKeyEnum.Swagger.value, None)
            openapi_type = OpenAPIVersionKeyEnum.Swagger.value

        if openapi_type_key:
            return SchemaValidateErr(f"{openapi_type_key} is not support", f"$.{openapi_type}", [openapi_type])
        return SchemaValidateErr("invalid openapi version", "", [])

    def parse(self):
        """
        解析 openapi
        """
        self._validate_refs(self.data)

        parse_result = ResolvingParser(
            spec_string=json.dumps(self.data), backend="openapi-spec-validator", strict=False
        )

        # 获取对应的parser
        parser = self._get_parser(parse_result)

        self.parser = parser
        self._raw_resource_list = parser.get_resources()
        self._resource_list = ResourceDataConvertor(self.gateway, self._raw_resource_list).convert()

    @staticmethod
    def _validate_refs(data: Dict[str, Any]) -> None:
        """校验 openapi 数据中所有 $ref 值，仅允许文档内部引用（以 # 开头）。

        防止通过外部 URL 或文件路径引用导致 SSRF / 本地文件读取。
        """
        if OpenAPIImportManager._has_unsafe_refs(data):
            raise ValueError("OpenAPI document contains external $ref which is not allowed")

    @staticmethod
    def _has_unsafe_refs(node: Any) -> bool:
        """迭代检查是否存在非文档内部 $ref 引用。"""
        stack: List[Any] = [node]

        while stack:
            current_node = stack.pop()
            if isinstance(current_node, dict):
                for key, value in current_node.items():
                    if key == "$ref":
                        if isinstance(value, str) and not value.startswith("#"):
                            return True
                    else:
                        stack.append(value)
            elif isinstance(current_node, list):
                stack.extend(current_node)

        return False

    def _get_parser(self, parse_result) -> BaseParser:
        if self.version == OPENAPIV2:
            return BaseParser(parse_result.specification, str(self.version))

        return OpenAPIV3Parser(parse_result.specification, str(self.version))

    def get_resource_list(self, raw=False):
        """
        获取解析之后的resource列表。
        raw：
        - true -> return List[Dict[str, Any]]
        - false -> List[ResourceData]
        """
        return self._raw_resource_list if raw else self._resource_list
