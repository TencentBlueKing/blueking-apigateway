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
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, List, Optional, Set, Tuple

from apigateway.biz.resource_doc.exceptions import OpenAPIDocGenerationError

from .models import (
    ExampleDoc,
    MediaTypeDoc,
    OperationDocContext,
    ParameterDoc,
    RequestBodyDoc,
    ResponseDoc,
    SchemaDoc,
    SchemaFieldDoc,
)

MAX_SCHEMA_DEPTH = 8
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")
CONSTRAINT_KEYS = (
    "enum",
    "default",
    "minimum",
    "exclusiveMinimum",
    "maximum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
)
MISSING = object()


class OperationDocBuilder:
    def __init__(self, openapi: Mapping[str, Any]):
        self.openapi = openapi

    def build(self) -> OperationDocContext:
        path, method, operation = self._get_operation()
        return OperationDocContext(
            operation_id=str(operation.get("operationId", "")),
            method=method.upper(),
            path=path,
            summary=self._table_text(operation.get("summary", "")),
            description=str(operation.get("description", "")).strip(),
            deprecated=bool(operation.get("deprecated", False)),
            tags=[self._table_text(tag) for tag in operation.get("tags", [])],
            parameters=self._build_parameters(operation.get("parameters", [])),
            request_body=self._build_request_body(operation.get("requestBody")),
            responses=self._build_responses(operation.get("responses", {})),
        )

    def _get_operation(self) -> Tuple[str, str, Mapping[str, Any]]:
        operations = []
        paths = self.openapi.get("paths", {})
        if isinstance(paths, Mapping):
            for path, path_item in paths.items():
                if not isinstance(path_item, Mapping):
                    continue
                for method, operation in path_item.items():
                    if str(method).lower() not in HTTP_METHODS or not isinstance(operation, Mapping):
                        continue
                    operations.append((str(path), str(method).lower(), operation))

        if len(operations) != 1:
            raise OpenAPIDocGenerationError(f"expected one OAS3 operation, found {len(operations)}")
        return operations[0]

    def _build_parameters(self, parameters: Any) -> List[ParameterDoc]:
        if not isinstance(parameters, list):
            return []
        return [self._build_parameter(parameter) for parameter in parameters if isinstance(parameter, Mapping)]

    def _build_parameter(
        self,
        parameter: Mapping[str, Any],
        *,
        name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> ParameterDoc:
        schema = parameter.get("schema", {})
        if not isinstance(schema, Mapping):
            schema = {}
        if not schema:
            content = parameter.get("content", {})
            if isinstance(content, Mapping):
                media: Any = next(iter(content.values()), {})
                if isinstance(media, Mapping) and isinstance(media.get("schema"), Mapping):
                    schema = media["schema"]

        example = parameter.get("example", MISSING)
        if example is MISSING:
            example = schema.get("example", MISSING)

        return ParameterDoc(
            name=self._table_text(name if name is not None else parameter.get("name", "")),
            location=self._table_text(location if location is not None else parameter.get("in", "")),
            type=self._table_text(self._schema_type(schema)),
            required=bool(parameter.get("required", False)),
            description=self._table_text(parameter.get("description", "")),
            default=self._table_display_value(schema.get("default", MISSING)),
            example=self._table_display_value(example),
            constraints=self._schema_constraints(schema),
        )

    def _build_request_body(self, request_body: Any) -> Optional[RequestBodyDoc]:
        if not isinstance(request_body, Mapping):
            return None
        return RequestBodyDoc(
            required=bool(request_body.get("required", False)),
            description=str(request_body.get("description", "")).strip(),
            contents=self._build_contents(request_body.get("content", {})),
        )

    def _build_responses(self, responses: Any) -> List[ResponseDoc]:
        if not isinstance(responses, Mapping):
            return []

        result = []
        for code, response in responses.items():
            if not isinstance(response, Mapping):
                continue
            status_code = str(code)
            headers = response.get("headers", {})
            result.append(
                ResponseDoc(
                    status_code=self._table_text(status_code),
                    status_text=self._status_text(status_code),
                    description=self._table_text(response.get("description", "")),
                    headers=(
                        [
                            self._build_parameter(header, name=str(name), location="header")
                            for name, header in headers.items()
                            if isinstance(header, Mapping)
                        ]
                        if isinstance(headers, Mapping)
                        else []
                    ),
                    contents=self._build_contents(response.get("content", {})),
                )
            )
        return result

    def _build_contents(self, content: Any) -> List[MediaTypeDoc]:
        if not isinstance(content, Mapping):
            return []

        result = []
        for media_type, media in content.items():
            if not isinstance(media, Mapping):
                continue
            schema = media.get("schema")
            schema_mapping = schema if isinstance(schema, Mapping) else None
            result.append(
                MediaTypeDoc(
                    media_type=str(media_type),
                    schema=self._build_schema(schema_mapping),
                    examples=self._build_examples(media, schema_mapping),
                )
            )
        return result

    def _build_examples(
        self,
        media: Mapping[str, Any],
        schema: Optional[Mapping[str, Any]],
    ) -> List[ExampleDoc]:
        examples = media.get("examples")
        if isinstance(examples, Mapping) and examples:
            result = []
            for name, example in examples.items():
                if isinstance(example, Mapping):
                    value = example.get("value", MISSING)
                    summary = example.get("summary", "")
                else:
                    value = example
                    summary = ""
                result.append(
                    ExampleDoc(
                        name=self._table_text(name),
                        summary=self._table_text(summary),
                        value=self._display_value(value),
                    )
                )
            return result

        value = media.get("example", MISSING)
        if value is MISSING and schema is not None:
            value = schema.get("example", MISSING)
        if value is MISSING:
            return []
        return [ExampleDoc(name="", summary="", value=self._display_value(value))]

    def _build_schema(self, schema: Optional[Mapping[str, Any]]) -> Optional[SchemaDoc]:
        if schema is None:
            return None
        return SchemaDoc(
            type=self._schema_type(schema),
            description=self._table_text(schema.get("description", "")),
            fields=self._flatten_schema(schema),
            example=self._display_value(schema.get("example", MISSING)),
        )

    def _flatten_schema(self, schema: Mapping[str, Any]) -> List[SchemaFieldDoc]:
        fields: List[SchemaFieldDoc] = []
        seen_paths: Set[str] = set()
        self._walk_schema(
            schema,
            path="",
            required=False,
            depth=0,
            active=set(),
            fields=fields,
            seen_paths=seen_paths,
        )
        return fields

    def _walk_schema(
        self,
        schema: Mapping[str, Any],
        *,
        path: str,
        required: bool,
        depth: int,
        active: Set[int],
        fields: List[SchemaFieldDoc],
        seen_paths: Set[str],
    ) -> None:
        schema_id = id(schema)
        if schema_id in active:
            self._append_field(schema, path, required, "recursive", fields, seen_paths)
            return

        if path and depth >= MAX_SCHEMA_DEPTH:
            self._append_field(
                schema,
                path,
                required,
                f"max-depth: {MAX_SCHEMA_DEPTH}",
                fields,
                seen_paths,
            )
            return

        if path:
            self._append_field(schema, path, required, "", fields, seen_paths)

        active.add(schema_id)
        try:
            if self._is_array(schema):
                items = schema.get("items")
                if isinstance(items, Mapping):
                    self._walk_schema(
                        items,
                        path=f"{path}[]",
                        required=False,
                        depth=depth + 1,
                        active=active,
                        fields=fields,
                        seen_paths=seen_paths,
                    )

            properties, required_names = self._properties_and_required(schema)
            for name, property_schema in properties:
                property_path = f"{path}.{name}" if path else name
                self._walk_schema(
                    property_schema,
                    path=property_path,
                    required=name in required_names,
                    depth=depth + 1,
                    active=active,
                    fields=fields,
                    seen_paths=seen_paths,
                )
        finally:
            active.remove(schema_id)

    def _append_field(
        self,
        schema: Mapping[str, Any],
        path: str,
        required: bool,
        marker: str,
        fields: List[SchemaFieldDoc],
        seen_paths: Set[str],
    ) -> None:
        if not path or path in seen_paths:
            return
        seen_paths.add(path)
        constraints = self._schema_constraints(schema)
        if marker:
            constraints = "<br>".join(value for value in (constraints, marker) if value)
        fields.append(
            SchemaFieldDoc(
                path=self._table_text(path),
                type=self._table_text(self._schema_type(schema)),
                required=required,
                description=self._table_text(schema.get("description", "")),
                constraints=constraints,
                example=self._table_display_value(schema.get("example", MISSING)),
            )
        )

    def _properties_and_required(
        self,
        schema: Mapping[str, Any],
    ) -> Tuple[List[Tuple[str, Mapping[str, Any]]], Set[str]]:
        properties: List[Tuple[str, Mapping[str, Any]]] = []
        required_names: Set[str] = set()
        visited: Set[int] = set()

        def collect(current: Mapping[str, Any]) -> None:
            current_id = id(current)
            if current_id in visited:
                return
            visited.add(current_id)

            required = current.get("required", [])
            if isinstance(required, list):
                required_names.update(str(name) for name in required)

            current_properties = current.get("properties", {})
            if isinstance(current_properties, Mapping):
                properties.extend(
                    (str(name), value) for name, value in current_properties.items() if isinstance(value, Mapping)
                )

            for keyword in ("allOf", "oneOf", "anyOf"):
                branches = current.get(keyword, [])
                if isinstance(branches, list):
                    for branch in branches:
                        if isinstance(branch, Mapping):
                            collect(branch)

        collect(schema)
        return properties, required_names

    def _schema_type(
        self,
        schema: Mapping[str, Any],
        active: Optional[Set[int]] = None,
        depth: int = 0,
    ) -> str:
        if active is None:
            active = set()
        schema_id = id(schema)
        if schema_id in active or depth >= MAX_SCHEMA_DEPTH:
            return "unknown"

        active.add(schema_id)
        try:
            composition_type = self._composition_type(schema, active, depth)
            if composition_type:
                return composition_type

            base_type, nullable = self._declared_type(schema)
            return self._decorate_type(schema, base_type, nullable, active, depth)
        finally:
            active.remove(schema_id)

    def _composition_type(self, schema: Mapping[str, Any], active: Set[int], depth: int) -> str:
        for keyword, separator in (("oneOf", " | "), ("anyOf", " | "), ("allOf", " & ")):
            branches = schema.get(keyword)
            if not isinstance(branches, list) or not branches:
                continue
            types = [
                self._schema_type(branch, active, depth + 1) for branch in branches if isinstance(branch, Mapping)
            ]
            if types:
                return f"{keyword}<{separator.join(types)}>"
        return ""

    @staticmethod
    def _declared_type(schema: Mapping[str, Any]) -> Tuple[str, bool]:
        raw_type = schema.get("type")
        nullable = bool(schema.get("nullable", False))
        if isinstance(raw_type, list):
            type_names = [str(value) for value in raw_type]
            nullable = nullable or "null" in type_names
            non_null_types = [value for value in type_names if value != "null"]
            return " | ".join(non_null_types) if non_null_types else "null", nullable
        if isinstance(raw_type, str):
            return raw_type, nullable or raw_type == "null"
        if isinstance(schema.get("properties"), Mapping) or isinstance(
            schema.get("additionalProperties"), (bool, Mapping)
        ):
            return "object", nullable
        return "unknown", nullable

    def _decorate_type(
        self,
        schema: Mapping[str, Any],
        base_type: str,
        nullable: bool,
        active: Set[int],
        depth: int,
    ) -> str:
        if base_type == "array":
            items = schema.get("items")
            item_type = self._schema_type(items, active, depth + 1) if isinstance(items, Mapping) else "unknown"
            base_type = f"array<{item_type}>"
        elif base_type == "object" and not schema.get("properties"):
            additional_properties = schema.get("additionalProperties")
            if isinstance(additional_properties, Mapping):
                value_type = self._schema_type(additional_properties, active, depth + 1)
                base_type = f"map<string, {value_type}>"
            elif additional_properties is True:
                base_type = "map<string, unknown>"
        elif base_type not in {"object", "null", "unknown"} and " | " not in base_type:
            schema_format = schema.get("format")
            if schema_format:
                base_type = f"{base_type}<{schema_format}>"

        if nullable and "null" not in base_type.split(" | "):
            return f"{base_type} | null"
        return base_type

    def _schema_constraints(self, schema: Mapping[str, Any]) -> str:
        values = []
        for key in CONSTRAINT_KEYS:
            value = schema.get(key, MISSING)
            if value is MISSING:
                continue
            values.append(f"{key}: {self._table_display_value(value)}")
        return "<br>".join(values)

    @staticmethod
    def _is_array(schema: Mapping[str, Any]) -> bool:
        raw_type = schema.get("type")
        return raw_type == "array" or isinstance(raw_type, list) and "array" in raw_type

    @staticmethod
    def _status_text(code: str) -> str:
        if not code.isdigit():
            return ""
        try:
            return HTTPStatus(int(code)).phrase
        except ValueError:
            return ""

    @staticmethod
    def _display_value(value: Any) -> str:
        if value is MISSING:
            return ""
        if isinstance(value, (dict, list)) or value is None or isinstance(value, (bool, int, float)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
        return str(value)

    @classmethod
    def _table_display_value(cls, value: Any) -> str:
        return cls._table_text(cls._display_value(value))

    @staticmethod
    def _table_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).replace("|", r"\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
