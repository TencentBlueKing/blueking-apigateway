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
import logging
import pkgutil
from collections import defaultdict
from typing import Any, Dict, List, Optional

import jsonschema

from apigateway.biz.constants import SwaggerFormatEnum
from apigateway.common.exceptions import SchemaValidationError
from apigateway.common.timeout import convert_timeout
from apigateway.core.constants import DEFAULT_BACKEND_NAME, HTTP_METHOD_ANY, ProxyTypeEnum
from apigateway.utils.yaml import yaml_export_dumps, yaml_loads

from .constants import VALID_METHOD_IN_SWAGGER_PATHITEM, SwaggerExtensionEnum

logger = logging.getLogger(__name__)


def load_swagger_schema():
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/schemas/v2.0/schema.json
    """
    data = pkgutil.get_data("apigateway.biz.resource.importer", "schema.json")
    return json.loads(data.decode("utf-8"))


def format_as_index(indices):
    """
    Construct a single string containing indexing operations for the indices.

    For example, [1, 2, "foo"] -> [1][2]["foo"]
    """
    if not indices:
        return ""
    return "[%s]" % "][".join(repr(index) for index in indices)


def format_json_schema_error(error):
    return f"{format_as_index(error.absolute_path)}: {error.message}"


class SwaggerManager:
    def __init__(self, swagger_data: Dict[str, Any]):
        self._swagger_data = swagger_data

    @classmethod
    def load_from_swagger(cls, swagger: str) -> "SwaggerManager":
        swagger_format = cls.guess_swagger_format(swagger)
        if swagger_format == SwaggerFormatEnum.JSON:
            return cls(swagger_data=json.loads(swagger))

        return cls(swagger_data=yaml_loads(swagger))

    @classmethod
    def guess_swagger_format(cls, swagger: str) -> SwaggerFormatEnum:
        # 内容以 "{" 开头，则为 json 串，否则为 yaml 串
        if swagger.strip().startswith("{"):
            return SwaggerFormatEnum.JSON

        return SwaggerFormatEnum.YAML

    def validate(self):
        try:
            jsonschema.validate(instance=self._swagger_data, schema=load_swagger_schema())
        except (jsonschema.ValidationError, jsonschema.SchemaError) as e:
            raise SchemaValidationError(format_json_schema_error(e))
        except Exception as e:
            logger.exception("failed to validate swagger.")
            raise SchemaValidationError(str(e))

    def get_paths(self) -> Dict[str, Any]:
        paths = self._swagger_data["paths"]
        paths = self._remove_invalid_method(paths)
        return self._add_base_path_to_path(self._swagger_data.get("basePath", "/"), paths)

    @classmethod
    def to_swagger(
        cls,
        paths: Dict[str, Any],
        swagger_format: SwaggerFormatEnum,
        version: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        info = {
            "version": version,
            "title": title,
            "description": description,
        }

        content = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {key: value for key, value in info.items() if value is not None},
            "schemes": ["http"],
            "paths": paths,
        }

        if swagger_format == SwaggerFormatEnum.JSON:
            return json.dumps(content, indent=4)

        return yaml_export_dumps(content)

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


class ResourceSwaggerImporter:
    def __init__(self, content: str):
        self.swagger_manager = SwaggerManager.load_from_swagger(content.strip())

    def validate(self):
        self.swagger_manager.validate()

    def get_resources(self):
        resources = []
        for path, path_item in self.swagger_manager.get_paths().items():
            for method_raw, operation in path_item.items():
                method = self._adapt_method(method_raw)

                extension_resource = operation.get(SwaggerExtensionEnum.RESOURCE.value, {})

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
                }

                resources.append(resource)

        return resources

    def _adapt_method(self, method: str) -> str:
        """
        适配 method
        """
        if method == SwaggerExtensionEnum.METHOD_ANY.value:
            return HTTP_METHOD_ANY

        return method.upper()

    def _adapt_backend(self, backend: Dict) -> Dict:
        """
        适配后端配置
        """
        backend_type = backend.get("type", ProxyTypeEnum.HTTP.value).lower()
        if backend_type != ProxyTypeEnum.HTTP.value:
            raise ValueError(f"unsupported backend type: {backend['type']}")

        timeout = convert_timeout(backend.get("timeout", 0))
        return {
            "method": backend["method"].upper(),
            "path": backend["path"],
            "match_subpath": backend.get("matchSubpath", False),
            "timeout": timeout,
            # 1.13 版本: 兼容旧版 (api_version=0.1) 资源 yaml 通过 openapi 导入
            "legacy_upstreams": backend.get("upstreams"),
            "legacy_transform_headers": backend.get("transformHeaders"),
        }

    def _adapt_description(self, summary: Optional[str], description: Optional[str]):
        """与根据 swagger 协议生成资源文档保持一致"""
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


class ResourceSwaggerExporter:
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

    def to_swagger(self, resources: list, file_type: str = "") -> str:
        content = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {
                "version": self.api_version,
                "title": self.title,
                "description": self.description,
            },
            "schemes": ["http"],
            "paths": self._generate_paths(resources),
        }

        if file_type == SwaggerFormatEnum.JSON.value:
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

        operation[SwaggerExtensionEnum.RESOURCE.value] = {
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
                    # TODO: 测试，如果 plugin_config.yaml 换行，导出的 yaml 格式是否符合预期
                    "yaml": plugin_config.yaml,
                }
                for plugin_config in resource.get("plugin_configs", [])
            ],
            "authConfig": self._adapt_auth_config(resource["auth_config"]),
            "descriptionEn": resource.get("description_en"),
        }

    def _adapt_method(self, method: str) -> str:
        if method == HTTP_METHOD_ANY:
            return SwaggerExtensionEnum.METHOD_ANY.value

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
                    "timeout": convert_timeout(backend["config"].get("timeout", 0)),
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
                    "timeout": convert_timeout(http_config["timeout"]),
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
