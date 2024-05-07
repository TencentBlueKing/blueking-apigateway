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
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from django.utils.translation import gettext as _
from pydantic import parse_obj_as

from apigateway.biz.constants import OpenAPIFormatEnum
from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData
from apigateway.biz.resource.importer.constants import VALID_METHOD_IN_SWAGGER_PATHITEM, OpenAPIExtensionEnum
from apigateway.biz.resource.importer.schema import (
    convert_swagger_formdata_to_openapi,
    convert_swagger_parameters_to_openapi,
    convert_swagger_response_headers_to_openapi,
)
from apigateway.biz.resource.models import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.core.constants import DEFAULT_BACKEND_NAME, HTTP_METHOD_ANY, ProxyTypeEnum
from apigateway.core.models import Backend, Gateway, Resource
from apigateway.utils.yaml import yaml_export_dumps


@dataclass
class BaseParser:
    """
    默认base_parser为 openapi
    """

    _openapi_data: Dict[str, Any]

    def get_resources(self) -> List[Dict[str, Any]]:
        resources = []
        for path, path_item in self.get_paths().items():
            for method_raw, operation in path_item.items():
                method = self._adapt_method(method_raw)

                extension_resource = operation.get(OpenAPIExtensionEnum.RESOURCE.value, {})

                backend = extension_resource.get("backend") or {
                    "type": ProxyTypeEnum.HTTP.value,
                    "method": method,
                    "path": path,
                }

                resource = {
                    "method": method,
                    "path": path,
                    "match_subpath": extension_resource.get("matchSubpath", False),
                    "name": operation["operationId"],
                    "description": self._adapt_description(operation.get("summary"), operation.get("description")),
                    "description_en": extension_resource.get("descriptionEn"),
                    "labels": operation.get("tags", []),
                    "is_public": extension_resource.get("isPublic", True),
                    "allow_apply_permission": extension_resource.get("allowApplyPermission", True),
                    "auth_config": self._adapt_auth_config(extension_resource.get("authConfig", {})),
                    "backend_name": backend.get("name", DEFAULT_BACKEND_NAME),
                    "backend_config": self._adapt_backend(backend),
                    # pluginConfigs 不存在或为 None，表示不处理此资源的插件配置的导入
                    "plugin_configs": extension_resource.get("pluginConfigs"),
                    # schema
                    "openapi_schema": self._get_openapi_schema(operation),
                }

                resources.append(resource)

        return resources

    def get_paths(self):
        paths = self._openapi_data["paths"]
        paths = self._remove_invalid_method(paths)
        return self._add_base_path_to_path(self._get_base_path(), paths)

    def _get_base_path(self):
        return self._openapi_data.get("basePath", "/")

    def _get_openapi_schema(self, operation: Dict[str, Any]):
        """
        获取api的schema
        eg:
        {
          "requestBody": {
          },
          "parameters": [

          ],
          "responses": {

          }
        }
        """
        openapi_schema = {}
        request_body = self._get_request_body(operation)
        if len(request_body) > 0:
            openapi_schema["requestBody"] = request_body

        parameters = self._get_parameters(operation)
        if len(parameters) > 0:
            openapi_schema["parameters"] = parameters

        responses = self._get_responses(operation)

        if len(responses) > 0:
            openapi_schema["responses"] = responses

        return openapi_schema

    def _get_parameters(self, operation: Dict[str, Any]):
        """
        获取非body请求参数
        """
        parameters = operation.get("parameters", [])

        without_body_parameters = [
            parameter
            for parameter in parameters
            if parameter.get("in", "") != "body" and parameter.get("in", "") != "formData"
        ]

        return convert_swagger_parameters_to_openapi(without_body_parameters)

    def _get_request_body(self, operation: Dict[str, Any]):
        """
         获取请求body,按照openapi3.0的格式返回
         return:
          eg:
           {
              "description": "Created user object",
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "integer",
                        "format": "int64",
                        "example": 10
                      },
                      "username": {
                        "type": "string",
                        "example": "theUser"
                      }
                    }
                  }
                }
              }
        }
        """

        # 如果没有配置，默认为：application/json

        content_types = operation.get("consumes", ["application/json"])

        parameters = operation.get("parameters", [])

        parameter_schema = {}
        std_parameters = {}

        # formdata参数
        form_data_params = []
        for parameter_item in parameters:
            if parameter_item.get("in", "") == "body":
                parameter_schema = parameter_item.get("schema", {})
                std_parameters["description"] = parameter_item.get("description", "")
                if "required" in parameter_item:
                    std_parameters["required"] = parameter_item["required"]
                break
            if parameter_item.get("in", "") == "formData":
                form_data_params.append(parameter_item)

        content = {}
        for content_type in content_types:
            if len(parameter_schema) > 0:
                content[content_type] = {"schema": parameter_schema}

        if len(content) > 0:
            std_parameters["content"] = content

        if len(std_parameters) == 0 and len(form_data_params) > 0:
            std_parameters = convert_swagger_formdata_to_openapi(form_data_params, content_types)

        return std_parameters

    def _get_responses(self, operation: Dict[str, Any]):
        """
        获取response,按照openapi3.0的格式返回
        {
          "200": {
            "description": "successful operation",
            "content": {
              "application/json": {
                "schema": {
                 }
              },
              "application/xml": {
                "schema": {
                }
              }
            }
          }
        }
        """
        openapi_v3_response = {}
        produces = operation.get("produces", ["application/json"])
        for status_code, response in operation.get("responses", {}).items():
            # OpenAPI 3.0 uses 'content' instead of 'schema' for the response body
            content = response.get("schema", {})
            for produce in produces:
                openapi_v3_response[status_code] = {
                    "description": response.get("description", "default response"),
                    "content": {produce: {"schema": content}},
                }
                if "headers" in response:
                    openapi_v3_response[status_code]["headers"] = convert_swagger_response_headers_to_openapi(
                        response.get("headers")
                    )
                if "examples" in response:
                    openapi_v3_response[status_code]["examples"] = response.get("examples")

        return openapi_v3_response

    def _add_base_path_to_path(self, base_path: str, paths: Dict[str, Any]) -> Dict[str, Any]:
        """将 base_path 添加到 path"""
        new_paths = {}
        for path, path_item in paths.items():
            new_path = self._join_path(base_path, path)
            new_paths[new_path] = path_item

        return new_paths

    def _remove_invalid_method(self, paths: Dict[str, Any]) -> Dict[str, Any]:
        """去除无效的 method"""
        valid_paths: Dict[str, Dict[str, Any]] = defaultdict(dict)
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in VALID_METHOD_IN_SWAGGER_PATHITEM:
                    continue
                valid_paths[path][method] = operation

        return valid_paths

    def _join_path(self, base_path: str, path: str) -> str:
        return "{}/{}".format(base_path.rstrip("/"), path.lstrip("/"))

    def _adapt_method(self, method: str) -> str:
        """
        适配 method
        """
        if method == OpenAPIExtensionEnum.METHOD_ANY.value:
            return HTTP_METHOD_ANY

        return method.upper()

    def _adapt_backend(self, backend: Dict) -> Dict:
        """
        适配后端配置
        """
        backend_type = backend.get("type", ProxyTypeEnum.HTTP.value).lower()
        if backend_type != ProxyTypeEnum.HTTP.value:
            raise ValueError(f"unsupported backend type: {backend['type']}")

        return {
            "method": backend["method"].upper(),
            "path": backend["path"],
            "match_subpath": backend.get("matchSubpath", False),
            "timeout": backend.get("timeout", 0),
            # 1.13 版本: 兼容旧版 (api_version=0.1) 资源 yaml 通过 openapi 导入
            "legacy_upstreams": backend.get("upstreams"),
            "legacy_transform_headers": backend.get("transformHeaders"),
        }

    def _adapt_description(self, summary: Optional[str], description: Optional[str]):
        """与根据 openapi 协议生成资源文档保持一致"""
        parts = []

        if summary:
            parts.append(summary)

        if description:
            parts.append(description)

        return "\n\n".join(parts)

    def _adapt_auth_config(self, auth_config: dict):
        config = {
            "auth_verified_required": auth_config.get("userVerifiedRequired", True),
            "app_verified_required": auth_config.get("appVerifiedRequired", True),
            "resource_perm_required": auth_config.get("resourcePermissionRequired", True),
        }

        if config["app_verified_required"] is False:
            config["resource_perm_required"] = False

        return config


class OpenAPIV3Parser(BaseParser):
    def _get_base_path(self):
        """
        对于 openapi3.0,basePath默认选择
        servers的第一个
        "servers": [
           {
           "url": "https://petstore3.swagger.io/api/v3"
           }
         ],
        """
        servers = self._openapi_data.get("servers", [])
        if len(servers) == 0:
            return "/"
        parsed_url = urlparse(servers[0].get("url", "/"))
        return parsed_url.path

    def _get_openapi_schema(self, operation: Dict[str, Any]):
        openapi_schema = {}
        if "parameters" in operation:
            openapi_schema["parameters"] = operation.get("parameters", [])

        if "requestBody" in operation:
            openapi_schema["requestBody"] = operation.get("requestBody", [])

        if "responses" in operation:
            openapi_schema["responses"] = operation.get("responses", [])

        return openapi_schema


class ResourceDataConvertor:
    def __init__(self, gateway: Gateway, resources: List[Dict[str, Any]]):
        """
        将资源数据转换为 ResourceData

        :param resources: 资源数据，可由 openapi yaml 解析而来或者自主构造。样例：
            {
                "id": 1,  # 可为 None
                "method": "GET",
                "path": "/v1/test",
                "match_subpath": False,
                "name": "test",
                "description": "test",
                "is_public": True,
                "allow_apply_permission": True,
                "labels": ["label1", "label2"],
                "auth_config": {
                    "app_verified_required": True,
                    "auth_verified_required": True,
                    "resource_perm_required": True,
                },
                "backend_name": "default",
                "backend_config": {
                    "method": "GET",
                    "path": "/v1/test",
                    "match_subpath": False,
                    "timeout": 0
                },
                "plugin_configs": [
                    {
                        "type": "bk-cors",
                        "yaml": "xxx",
                    }
                ]
            }
        """
        self.gateway = gateway
        self.resources = resources

    def convert(self) -> List[ResourceData]:
        resource_objs = list(Resource.objects.filter(gateway=self.gateway))
        resource_id_to_resource_obj = {resource.id: resource for resource in resource_objs}
        resource_key_to_resource_obj = {f"{resource.method}:{resource.path}": resource for resource in resource_objs}
        backends = {backend.name: backend for backend in Backend.objects.filter(gateway=self.gateway)}

        resource_data_list = []
        for resource in self.resources:
            resource_obj = self._get_resource_obj(resource, resource_id_to_resource_obj, resource_key_to_resource_obj)

            metadata = resource.get("metadata", {})
            # 是否为新增资源
            metadata["is_created"] = not resource_obj
            # 标签名
            metadata["labels"] = resource.get("labels", [])

            backend_name = resource.get("backend_name", DEFAULT_BACKEND_NAME)
            backend = backends.get(backend_name)
            if not backend:
                raise ValueError(_("后端服务 (name={name}) 不存在。").format(name=backend_name))

            resource_data_list.append(
                ResourceData(
                    resource=resource_obj,
                    name=resource["name"],
                    description=resource.get("description", ""),
                    description_en=resource.get("description_en", None),
                    method=resource["method"],
                    path=resource["path"],
                    match_subpath=resource.get("match_subpath", False),
                    is_public=resource.get("is_public", True),
                    allow_apply_permission=resource.get("allow_apply_permission", True),
                    auth_config=ResourceAuthConfig.parse_obj(resource.get("auth_config", {})),
                    backend=backend,
                    backend_config=ResourceBackendConfig.parse_obj(resource["backend_config"]),
                    plugin_configs=parse_obj_as(Optional[List[PluginConfigData]], resource.get("plugin_configs")),
                    # 在导入时，根据 metadata 中的 labels 创建 GatewayLabel，并补全 label_ids 数据
                    label_ids=[],
                    metadata=metadata,
                    openapi_schema=resource.get("openapi_schema", {}),
                )
            )

        return resource_data_list

    def _get_resource_obj(
        self,
        resource: Dict[str, Any],
        resource_id_to_resource_obj: Dict[int, Resource],
        resource_key_to_resource_obj: Dict[str, Resource],
    ) -> Optional[Resource]:
        if resource.get("id") is not None:
            if resource["id"] not in resource_id_to_resource_obj:
                raise ValueError("资源 (id={id}) 不存在。".format(id=resource["id"]))

            return resource_id_to_resource_obj[resource["id"]]

        key = f"{resource['method']}:{resource['path']}"
        return resource_key_to_resource_obj.get(key)


class BaseExporter:
    """
    openapi 导出器
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

    def to_openapi(self, resources: list, file_type: str = "") -> str:
        content = self._get_openapi_content(resources)

        if file_type == OpenAPIFormatEnum.JSON.value:
            return json.dumps(content, indent=4)

        return yaml_export_dumps(content)

    def _get_openapi_content(self, resources: list) -> Dict[str, Any]:
        return {
            "openapi": "3.0.1",
            "servers": [{"url": "/"}],
            "info": {
                "version": self.api_version,
                "title": self.title,
                "description": self.description,
            },
            "paths": self._generate_paths(resources),
        }

    def get_swagger_by_paths(
        self,
        paths: Dict[str, Any],
        openapi_format: OpenAPIFormatEnum,
    ) -> str:
        info = {
            "version": self.api_version,
            "title": self.title,
            "description": self.description,
        }

        content = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {key: value for key, value in info.items() if value is not None},
            "schemes": ["http"],
            "paths": paths,
        }

        if openapi_format == OpenAPIFormatEnum.JSON:
            return json.dumps(content, indent=4)

        return yaml_export_dumps(content)

    def _generate_paths(self, resources: List[Dict]) -> Dict[str, Any]:
        paths: Dict[str, Any] = {}
        for resource in resources:
            path = resource["path"]
            paths.setdefault(path, {})

            method = self._adapt_method(resource["method"])
            operation = {
                "operationId": resource["name"],
                "description": resource["description"],
                "tags": resource.get("labels", []),
            }

            # schema
            schema_obj = resource.get("schema", None)
            schema = schema_obj.schema if schema_obj else {}
            self._generate_openapi_schema(operation, schema)

            if self.include_bk_apigateway_resource:
                self._generate_bk_apigateway_resource(operation, resource)

            paths[path][method] = operation

        return paths

    def get_swagger_by_resource(self, resources: List[Dict], file_type: str = ""):
        content = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {
                "version": self.api_version,
                "title": self.title,
                "description": self.description,
            },
            "schemes": ["http"],
            "paths": self._gen_swagger_paths(resources),
        }

        if file_type == OpenAPIFormatEnum.JSON.value:
            return json.dumps(content, indent=4)

        return yaml_export_dumps(content)

    def _gen_swagger_paths(self, resources: List[Dict]) -> Dict[str, Any]:
        paths: Dict[str, Any] = {}
        for resource in resources:
            path = resource["path"]
            paths.setdefault(path, {})

            method = self._adapt_method(resource["method"])
            operation = {
                "operationId": resource["name"],
                "description": resource["description"],
                "tags": resource.get("labels", []),
                "responses": {
                    "default": {"description": ""},
                },
            }

            if self.include_bk_apigateway_resource:
                self._generate_bk_apigateway_resource(operation, resource)

            paths[path][method] = operation
        return paths

    def _generate_openapi_schema(self, operation: Dict[str, Any], schema: Dict[str, Any]):
        operation.update(schema)

    def _generate_bk_apigateway_resource(self, operation: Dict[str, Any], resource: Dict[str, Any]):
        backend = resource.get("backend", {})

        operation[OpenAPIExtensionEnum.RESOURCE.value] = {
            "isPublic": resource["is_public"],
            "allowApplyPermission": resource["allow_apply_permission"],
            "matchSubpath": resource.get("match_subpath", False),
            "backend": self._adapt_backend(
                backend,
                resource.get("proxy_type", ""),
                resource.get("proxy_configs", {}),
            ),
            "pluginConfigs": [
                {
                    "type": plugin_config.type.code,
                    "yaml": plugin_config.yaml,
                }
                for plugin_config in resource.get("plugin_configs", [])
            ],
            "authConfig": self._adapt_auth_config(resource["auth_config"]),
            "descriptionEn": resource.get("description_en"),
        }

    def _adapt_method(self, method: str) -> str:
        if method == HTTP_METHOD_ANY:
            return OpenAPIExtensionEnum.METHOD_ANY.value

        return method.lower()

    def _adapt_backend(self, backend: Dict, proxy_type: str, proxy_configs: Dict) -> Dict:
        result = {}

        if backend.get("name"):
            result["name"] = backend["name"]

        if proxy_type:
            result["type"] = proxy_type.upper()

        if backend.get("config"):
            result.update(
                {
                    "method": backend["config"]["method"].lower(),
                    "path": backend["config"]["path"],
                    "matchSubpath": backend["config"].get("match_subpath", False),
                    "timeout": backend["config"].get("timeout", 0),
                }
            )
            return result

        if proxy_type == ProxyTypeEnum.HTTP.value:
            http_config = proxy_configs[ProxyTypeEnum.HTTP.value]
            result.update(
                {
                    "method": http_config["method"].lower(),
                    "path": http_config["path"],
                    "matchSubpath": http_config.get("match_subpath", False),
                    "timeout": http_config["timeout"],
                    "upstreams": http_config.get("upstreams", {}),
                    "transformHeaders": http_config.get("transform_headers", {}),
                }
            )
        else:
            raise ValueError(f"unsupported proxy_type: {proxy_type}")

        return result

    def _adapt_auth_config(self, auth_config: Dict) -> Dict:
        config = {
            "userVerifiedRequired": auth_config.get("auth_verified_required", True),
            "appVerifiedRequired": auth_config.get("app_verified_required", True),
            "resourcePermissionRequired": auth_config.get("resource_perm_required", True),
        }

        if config["appVerifiedRequired"] is False:
            config["resourcePermissionRequired"] = False

        return config
