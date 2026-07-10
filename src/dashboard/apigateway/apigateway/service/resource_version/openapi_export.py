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
"""OpenAPI export helpers for resource-version data."""

import copy
import json
from typing import TYPE_CHECKING, Any, Dict, List

from openapi_spec_validator.versions import OPENAPIV31

from apigateway.apps.support.constants import OpenAPIFormatEnum
from apigateway.core.constants import HTTP_METHOD_ANY, ProxyTypeEnum
from apigateway.service.backend import get_backend_id_to_instance
from apigateway.service.resource import get_gateway_resource_id_to_labels
from apigateway.utils.yaml import yaml_dumps, yaml_export_dumps

from .schema import get_resource_id_to_schema_by_resource_version

if TYPE_CHECKING:
    from apigateway.core.models import ResourceVersion

OPENAPI_METHOD_ANY_EXTENSION = "x-bk-apigateway-method-any"
OPENAPI_RESOURCE_EXTENSION = "x-bk-apigateway-resource"


def has_openapi_schema(openapi_schema: Dict[str, Any]) -> bool:
    if "none_schema" in openapi_schema and openapi_schema["none_schema"] is True:
        return True

    if "requestBody" in openapi_schema or "parameters" in openapi_schema:
        return True

    return False


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
        return self.serialize_openapi(self.get_openapi_content(resources), file_type)

    def get_openapi_content(self, resources: list) -> Dict[str, Any]:
        return self._get_openapi_content(resources)

    def serialize_openapi(self, content: Dict[str, Any], file_type: str = "") -> str:

        if file_type == OpenAPIFormatEnum.JSON.value:
            # 设置 ensure_ascii=False,防止中文被编码
            return json.dumps(content, indent=4, ensure_ascii=False)

        return yaml_export_dumps(content)

    def _get_openapi_content(self, resources: list) -> Dict[str, Any]:
        openapi_version = "3.0.1"
        if resources and resources[0].get("openapi_schema", {}).get("version") == str(OPENAPIV31):
            openapi_version = "3.1.0"

        return {
            "openapi": openapi_version,
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
            schema = resource.get("openapi_schema", {})

            # remove openapi version
            if "version" in schema:
                del schema["version"]
            # remove none_schema flag, 这个字段属于非openapi标准字段，不移除会导致生成文档有一次以及导出的yaml不合法
            if "none_schema" in schema:
                resource["none_schema"] = schema["none_schema"]
                del schema["none_schema"]
            elif has_openapi_schema(schema):
                resource["none_schema"] = False

            operation.update(schema)

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

    def _generate_bk_apigateway_resource(self, operation: Dict[str, Any], resource: Dict[str, Any]):
        backend = resource.get("backend", {})

        operation[OPENAPI_RESOURCE_EXTENSION] = {
            "isPublic": resource["is_public"],
            "allowApplyPermission": resource["allow_apply_permission"],
            "matchSubpath": resource.get("match_subpath", False),
            "enableWebsocket": resource.get("enable_websocket", False),
            "backend": self._adapt_backend(
                backend,
                resource.get("proxy_type", ""),
                resource.get("proxy_configs", {}),
            ),
            # 资源配置导出时 plugin_config 是 PluginConfig 对象，资源版本导出时是 dict
            "pluginConfigs": [
                {
                    "type": plugin_config["type"] if isinstance(plugin_config, dict) else plugin_config.type.code,
                    "yaml": plugin_config["yaml"] if isinstance(plugin_config, dict) else plugin_config.yaml,
                }
                for plugin_config in resource.get("plugin_configs", [])
            ],
            "authConfig": self._adapt_auth_config(resource["auth_config"]),
            "descriptionEn": resource.get("description_en"),
        }
        if resource.get("none_schema"):
            operation[OPENAPI_RESOURCE_EXTENSION]["noneSchema"] = resource.get("none_schema")

    def _adapt_method(self, method: str) -> str:
        if method == HTTP_METHOD_ANY:
            return OPENAPI_METHOD_ANY_EXTENSION

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
        self._exporter = BaseExporter(
            self.api_version, self.include_bk_apigateway_resource, self.title, self.description
        )

    def export_resource_version_openapi(self, resource_version: ResourceVersion, file_type: str = ""):
        """
        根据资源版本数据导出openapi
        """
        return self._exporter.serialize_openapi(self.get_resource_version_openapi(resource_version), file_type)

    def get_resource_version_openapi(self, resource_version: ResourceVersion) -> Dict[str, Any]:
        return self._exporter.get_openapi_content(self._build_resource_version_resources(resource_version))

    def _build_resource_version_resources(self, resource_version: ResourceVersion) -> list[Dict[str, Any]]:
        backend_id_to_config = get_backend_id_to_instance(resource_version.gateway.id)
        resource_labels = get_gateway_resource_id_to_labels(resource_version.gateway.id)
        resource_id_to_schema = get_resource_id_to_schema_by_resource_version(resource_version.id)

        resource_data_list = []
        for resource_snapshot in resource_version.data:
            resource = copy.deepcopy(resource_snapshot)
            labels = resource_labels.get(resource["id"], [])
            resource["labels"] = [label["name"] for label in labels]
            resource["openapi_schema"] = resource_id_to_schema.get(resource["id"], {})
            resource["auth_config"] = json.loads(resource["contexts"]["resource_auth"]["config"])
            resource["backend"] = {
                "name": backend_id_to_config[resource["proxy"]["backend_id"]].name,
                "config": json.loads(resource["proxy"]["config"]),
            }
            resource["plugin_configs"] = [
                {
                    "type": plugin["type"],
                    "yaml": yaml_dumps(plugin["config"]).rstrip("\n"),
                }
                for plugin in resource.get("plugins", [])
            ]
            resource_data_list.append(resource)

        return resource_data_list

    def export_openapi(self, resources: list, file_type: str = ""):
        """
        file_type: json/yaml
        """
        return self._exporter.to_openapi(resources, file_type)

    def get_swagger_by_paths(
        self,
        paths: Dict[str, Any],
        openapi_format: OpenAPIFormatEnum,
    ) -> str:
        """
        获取swagger2.0的格式导出(主要用于文档生成)
        """
        return self._exporter.get_swagger_by_paths(paths, openapi_format)

    def get_swagger_by_resources(self, resources: List[Dict], file_type: str = "") -> str:
        """
        获取swagger2.0的格式导出(主要用于sdk生成)
        """
        return self._exporter.get_swagger_by_resource(resources, file_type)
