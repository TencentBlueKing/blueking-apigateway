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

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import force_instance


class BkAutoSchema(AutoSchema):
    """Describe the Dashboard response envelope without changing API responses."""

    def _get_paginator(self):
        if self.method != "GET":
            return None
        paginator = super()._get_paginator()
        if paginator is not None:
            # Pagination has distinct Web/V2 and legacy V1 response contracts.
            paginator.request = self.view.request
        return paginator

    def _get_request_for_media_type(self, serializer, direction="request"):
        if self.method != "PATCH" or getattr(self.view, "schema_request_partial", True):
            return super()._get_request_for_media_type(serializer, direction)
        # Some PATCH handlers validate a full serializer instead of passing partial=True.
        component = self.resolve_serializer(force_instance(serializer), direction)
        if not component:
            return None, False
        readonly = {name for name, field in component.schema.get("properties", {}).items() if field.get("readOnly")}
        required = any(name not in readonly for name in component.schema.get("required", []))
        return component.ref, required

    def _get_request_body(self, direction="request"):
        if self.method != "DELETE" or not getattr(self.view, "schema_delete_request_body", False):
            return super()._get_request_body(direction)
        # These existing batch APIs consume DELETE bodies; spectacular skips them by default.
        schema, _ = self._get_request_for_media_type(self.get_request_serializer(), direction)
        if schema is None:
            return None
        return {
            "content": {media_type: {"schema": schema} for media_type in self.map_parsers()},
            "required": True,
        }

    def _get_response_for_code(self, serializer, status_code, media_types=None, direction="response"):
        response = super()._get_response_for_code(serializer, status_code, media_types, direction)
        if direction != "response" or status_code == "204" or not getattr(self.view, "schema_response_envelope", True):
            return response
        for media_type, content in response.get("content", {}).items():
            if media_type != "application/json":
                continue
            schema = content["schema"]
            if self.view.__module__.startswith("apigateway.apis.open."):
                properties = {
                    "result": {"type": "boolean"},
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": schema,
                }
            else:
                key = "data" if status_code.startswith("2") else "error"
                properties = {key: schema}
            content["schema"] = {"type": "object", "properties": properties, "required": list(properties)}
        return response
