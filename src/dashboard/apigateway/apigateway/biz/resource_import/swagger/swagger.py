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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import jsonschema

from apigateway.biz.resource_import.swagger.helpers import (
    AuthConfigConverter,
    format_jsonschema_error,
    load_swagger_schema,
)
from apigateway.common.exceptions import SchemaValidationError
from apigateway.core.constants import (
    HTTP_METHOD_ANY,
    VALID_METHOD_IN_SWAGGER_PATHITEM,
    ProxyTypeEnum,
    SwaggerExtensionEnum,
    SwaggerFormatEnum,
)
from apigateway.utils.yaml import yaml_dumps, yaml_loads

logger = logging.getLogger(__name__)


@dataclass
class SwaggerManager:
    content: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load_from_swagger(cls, swagger: str) -> "SwaggerManager":
        swagger_format = cls.guess_swagger_format(swagger)
        if swagger_format == SwaggerFormatEnum.JSON:
            return cls(content=json.loads(swagger))

        return cls(content=yaml_loads(swagger))

    @classmethod
    def guess_swagger_format(cls, swagger: str) -> SwaggerFormatEnum:
        # 内容以 "{" 开头，则为 json 串，否则为 yaml 串
        if swagger.strip().startswith("{"):
            return SwaggerFormatEnum.JSON

        return SwaggerFormatEnum.YAML

    def validate(self):
        try:
            jsonschema.validate(instance=self.content, schema=load_swagger_schema())
        except (jsonschema.ValidationError, jsonschema.SchemaError) as e:
            raise SchemaValidationError(format_jsonschema_error(e))
        except Exception as e:
            logger.exception("failed to validate swagger.")
            raise SchemaValidationError(str(e))

    def get_paths(self) -> Dict[str, Any]:
        paths = self.content["paths"]
        paths = self._remove_invalid_method(paths)
        return self._add_base_path_to_path(self.content.get("basePath", "/"), paths)

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

        return yaml_dumps(content)

    def _add_base_path_to_path(self, base_path: str, paths: Dict[str, Any]) -> Dict[str, Any]:
        """将 base_path 添加到 path"""
        new_paths = {}
        for path, path_item in paths.items():
            path = self._join_path(base_path, path)
            new_paths[path] = path_item

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
            for method, operation in path_item.items():
                method = self._adapt_method(method)

                extension_resource = operation.get(SwaggerExtensionEnum.RESOURCE.value, {})

                backend = extension_resource.get("backend") or {
                    "type": ProxyTypeEnum.HTTP.value,
                    "method": method,
                    "path": path,
                }
                proxy_type, proxy_configs = self._adapt_backend(backend)

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
                    "proxy_type": proxy_type,
                    "proxy_configs": proxy_configs,
                    "auth_config": AuthConfigConverter.to_inner(extension_resource.get("authConfig", {})),
                    "disabled_stages": extension_resource.get("disabledStages", []),
                }

                resources.append(resource)

        return resources

    def _adapt_method(self, method):
        """
        适配 method
        """
        if method == SwaggerExtensionEnum.METHOD_ANY.value:
            return HTTP_METHOD_ANY
        return method.upper()

    def _adapt_backend(self, backend):
        """
        适配后端配置
        """
        proxy_type = backend["type"].lower()
        if proxy_type == ProxyTypeEnum.HTTP.value:
            return (
                proxy_type,
                {
                    ProxyTypeEnum.HTTP.value: {
                        "method": backend["method"].upper(),
                        "path": backend["path"],
                        "match_subpath": backend.get("matchSubpath", False),
                        "timeout": backend.get("timeout", 0),
                        "upstreams": backend.get("upstreams") or {},
                        "transform_headers": backend.get("transformHeaders") or {},
                    }
                },
            )

        elif proxy_type == ProxyTypeEnum.MOCK.value:
            return (
                proxy_type,
                {
                    ProxyTypeEnum.MOCK.value: {
                        "code": backend["statusCode"],
                        "body": backend.get("responseBody", ""),
                        "headers": backend.get("headers", {}),
                    }
                },
            )

        return None, {}

    def _adapt_description(self, summary: Optional[str], description: Optional[str]):
        """与根据 swagger 协议生成资源文档保持一致"""
        parts = []

        if summary:
            parts.append(summary)

        if description:
            parts.append(description)

        return "\n\n".join(parts)


@dataclass
class ResourceSwaggerExporter:
    api_version: str = "0.1"
    include_bk_apigateway_resource: bool = True
    title: str = "API Gateway Resources"
    description: str = ""

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
        return yaml_dumps(content)

    def _generate_bk_apigateway_resource(self, operation: Dict[str, Any], resource: Dict[str, Any]):
        operation[SwaggerExtensionEnum.RESOURCE.value] = {
            "isPublic": resource["is_public"],
            "allowApplyPermission": resource["allow_apply_permission"],
            "matchSubpath": resource.get("match_subpath", False),
            "backend": self._adapt_backend(
                resource["proxy_type"],
                resource["proxy_configs"],
            ),
            "authConfig": AuthConfigConverter.to_yaml(resource["auth_config"]),
            "disabledStages": resource["disabled_stages"],
            "descriptionEn": resource.get("description_en"),
        }

    def _generate_paths(self, resources):
        paths = {}
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

    def _adapt_method(self, method):
        if method == HTTP_METHOD_ANY:
            return SwaggerExtensionEnum.METHOD_ANY.value

        return method.lower()

    def _adapt_backend(self, proxy_type, proxy_configs):
        backend = {
            "type": proxy_type.upper(),
        }
        if proxy_type == ProxyTypeEnum.HTTP.value:
            http_config = proxy_configs[ProxyTypeEnum.HTTP.value]
            backend.update(
                {
                    "method": http_config["method"].lower(),
                    "path": http_config["path"],
                    "matchSubpath": http_config.get("match_subpath", False),
                    "timeout": http_config["timeout"],
                    "upstreams": http_config.get("upstreams", {}),
                    "transformHeaders": http_config.get("transform_headers", {}),
                }
            )

        elif proxy_type == ProxyTypeEnum.MOCK.value:
            mock_config = proxy_configs[ProxyTypeEnum.MOCK.value]
            backend.update(
                {
                    "statusCode": mock_config["code"],
                    "responseBody": mock_config.get("body", ""),
                    "headers": mock_config.get("headers", {}),
                }
            )

        return backend
