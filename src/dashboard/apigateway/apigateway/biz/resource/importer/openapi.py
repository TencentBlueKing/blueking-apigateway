# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from typing import Any, Dict, List

from openapi_spec_validator.validation.exceptions import UnresolvableParameterError
from openapi_spec_validator.versions import OPENAPIV2, get_spec_version
from openapi_spec_validator.versions.exceptions import OpenAPIVersionNotFound
from prance import ResolvingParser

from apigateway.biz.constants import OpenAPIFormatEnum
from apigateway.biz.resource.importer.constants import OpenAPIVersionKeyEnum
from apigateway.biz.resource.importer.parser import BaseExporter, BaseParser, OpenAPIV3Parser, ResourceDataConvertor
from apigateway.biz.resource.importer.schema import (
    SchemaValidateErr,
    get_apigw_schema_validator,
    set_openapi_parser_schema_validator,
)
from apigateway.biz.resource.importer.validate import ResourceImportValidator
from apigateway.biz.resource.models import ResourceData
from apigateway.core.models import Gateway
from apigateway.utils.yaml import yaml_loads


class OpenAPIImportManager:
    """
    资源配置导入manager
    """

    def __init__(self, gateway: Gateway, openapi_data: Dict[str, Any]):
        self.openapi_version = None
        self.openapi_data = openapi_data
        self.gateway = gateway
        self._raw_resource_list: List[Dict[str, Any]] = []
        self._resource_list: List[ResourceData] = []
        self.parser = None

    @classmethod
    def load_from_openapi_content(cls, gateway: Gateway, content: str) -> "OpenAPIImportManager":
        openapi_format = cls.guess_openapi_format(content)

        loads_func = yaml_loads
        if openapi_format == OpenAPIFormatEnum.JSON:
            loads_func = json.loads

        return cls(gateway=gateway, openapi_data=loads_func(content))

    @classmethod
    def guess_openapi_format(cls, open_api_config: str) -> OpenAPIFormatEnum:
        # 内容以 "{" 开头，则为 json 串，否则为 yaml 串
        if open_api_config.strip().startswith("{"):
            return OpenAPIFormatEnum.JSON

        return OpenAPIFormatEnum.YAML

    def validate(self) -> List[SchemaValidateErr]:
        """
        进行校验
        """
        try:
            # 先获取 openapi版本
            openapi_version = get_spec_version(self.openapi_data)
        except OpenAPIVersionNotFound:
            return [self._get_openapi_version_err()]

        self.openapi_version = openapi_version

        # 获取 openapi validator
        spec_validator = get_apigw_schema_validator(openapi_version)

        schema_validate_result = [
            SchemaValidateErr(
                err.message,
                err.json_path,
                list(err.absolute_path),
            )
            for err in spec_validator.cls(self.openapi_data).iter_errors()
            if not isinstance(err, UnresolvableParameterError)  # 需要排除路径参数校验
        ]

        if len(schema_validate_result) > 0:
            return schema_validate_result

        # 进行逻辑校验

        self.parse()

        validator = ResourceImportValidator(
            gateway=self.gateway,
            resource_data_list=self._resource_list,
            need_delete_unspecified_resources=False,
        )

        return validator.validate()

    def _get_openapi_version_err(self) -> SchemaValidateErr:
        """
        获取 openapi 版本校验失败的 SchemaValidateErr
        """
        openapi_type = OpenAPIVersionKeyEnum.OpenAPI.value
        openapi_type_key = self.openapi_data.get(OpenAPIVersionKeyEnum.OpenAPI.value, None)
        if not openapi_type_key:
            openapi_type_key = self.openapi_data.get(OpenAPIVersionKeyEnum.Swagger.value, None)
            openapi_type = OpenAPIVersionKeyEnum.Swagger.value

        if openapi_type_key:
            return SchemaValidateErr(f"{openapi_type_key} is not support", f"$.{openapi_type}", [openapi_type])
        return SchemaValidateErr("invalid openapi version", "", [])

    def parse(self):
        """
        解析 openapi
        """
        set_openapi_parser_schema_validator(self.openapi_version)

        parse_result = ResolvingParser(
            spec_string=str(self.openapi_data), backend="openapi-spec-validator", strict=False
        )

        # 获取对应的parser
        parser = self._get_parser(parse_result)

        self.parser = parser
        self._raw_resource_list = parser.get_resources()
        self._resource_list = ResourceDataConvertor(self.gateway, self._raw_resource_list).convert()

    def _get_parser(self, parse_result) -> BaseParser:
        if self.openapi_version == OPENAPIV2:
            return BaseParser(parse_result.specification)

        return OpenAPIV3Parser(parse_result.specification)

    def get_resource_list(self, raw=False):
        """
        获取解析之后的resource列表。
        raw：
        - true -> return List[Dict[str, Any]]
        - false -> List[ResourceData]
        """
        return self._raw_resource_list if raw else self._resource_list


class OpenAPIExportManager:
    """
    资源配置导出manager
    """

    def __init__(
        self,
        api_version: str = "2.0",
        include_bk_apigateway_resource: bool = True,
        title: str = "API Gateway Resources",
        description: str = "",
    ):
        self.api_version = api_version
        self.include_bk_apigateway_resource = include_bk_apigateway_resource
        self.title = title
        self.description = description

    def _get_exporter(self) -> BaseExporter:
        return BaseExporter(self.api_version, self.include_bk_apigateway_resource, self.title, self.description)

    def export_openapi(self, resources: list, file_type: str = ""):
        """
        file_type: json/yaml
        """
        return self._get_exporter().to_openapi(resources, file_type)

    def get_swagger_by_paths(
        self,
        paths: Dict[str, Any],
        openapi_format: OpenAPIFormatEnum,
    ) -> str:
        """
        获取swagger2.0的格式导出(主要用于文档生成)
        """
        return self._get_exporter().get_swagger_by_paths(paths, openapi_format)

    def get_swagger_by_resources(self, resources: List[Dict], file_type: str = "") -> str:
        """
        获取swagger2.0的格式导出(主要用于sdk生成)
        """
        return self._get_exporter().get_swagger_by_resource(resources, file_type)
