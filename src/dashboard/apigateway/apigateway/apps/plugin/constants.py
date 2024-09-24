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
from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _

from apigateway.core.constants import ScopeTypeEnum


class PluginTypeCodeEnum(StructuredEnum):
    BK_RATE_LIMIT = EnumField("bk-rate-limit", label=_("频率控制"))
    BK_CORS = EnumField("bk-cors", label="CORS")
    BK_HEADER_REWRITE = EnumField("bk-header-rewrite", label=_("Header 转换"))
    BK_IP_RESTRICTION = EnumField("bk-ip-restriction", label="ip-restriction")
    BK_STATUS_REWRITE = EnumField("bk-status-rewrite", label=_("网关错误使用HTTP状态码200(不推荐)"))
    BK_VERIFIED_USER_EXEMPTED_APPS = EnumField(
        "bk-verified-user-exempted-apps", label=_("免用户认证应用白名单(不推荐)")
    )
    BK_MOCK = EnumField("bk-mock", label=_("mocking 插件"))
    API_BREAKER = EnumField("api-breaker", label=_("API 熔断"))
    REQUEST_VALIDATION = EnumField("request-validation", label=_("请求校验"))


class PluginTypeScopeEnum(StructuredEnum):
    STAGE = EnumField(ScopeTypeEnum.STAGE.value, label=_("环境"))
    RESOURCE = EnumField(ScopeTypeEnum.RESOURCE.value, label=_("资源"))
    STAGE_AND_RESOURCE = EnumField("stage_and_resource", label=_("环境和资源"))
    # maybe more enum: gateway, all


class PluginBindingScopeEnum(StructuredEnum):
    STAGE = EnumField(ScopeTypeEnum.STAGE.value, label=_("环境"))
    RESOURCE = EnumField(ScopeTypeEnum.RESOURCE.value, label=_("资源"))


class PluginStyleEnum(StructuredEnum):
    RAW = EnumField("raw", label=_("原生"))
    DYNAMIC = EnumField("dynamic", label=_("动态"))
    FIX = EnumField("fix", label=_("固定"))


class PluginBindingSourceEnum(StructuredEnum):
    YAML_IMPORT = EnumField("yaml_import", label=_("yaml导入"))
    USER_CREATE = EnumField("user_create", label=_("用户创建"))


Draft7Schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "title": "Core schema meta-schema",
    "definitions": {
        "schemaArray": {"type": "array", "minItems": 1, "items": {"$ref": "#"}},
        "nonNegativeInteger": {"type": "integer", "minimum": 0},
        "nonNegativeIntegerDefault0": {"allOf": [{"$ref": "#/definitions/nonNegativeInteger"}, {"default": 0}]},
        "simpleTypes": {"enum": ["array", "boolean", "integer", "null", "number", "object", "string"]},
        "stringArray": {"type": "array", "items": {"type": "string"}, "uniqueItems": True, "default": []},
    },
    "type": ["object", "boolean"],
    "properties": {
        "$id": {"type": "string", "format": "uri-reference"},
        "$schema": {"type": "string", "format": "uri"},
        "$ref": {"type": "string", "format": "uri-reference"},
        "$comment": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "default": True,
        "readOnly": {"type": "boolean", "default": False},
        "writeOnly": {"type": "boolean", "default": False},
        "examples": {"type": "array", "items": True},
        "multipleOf": {"type": "number", "exclusiveMinimum": 0},
        "maximum": {"type": "number"},
        "exclusiveMaximum": {"type": "number"},
        "minimum": {"type": "number"},
        "exclusiveMinimum": {"type": "number"},
        "maxLength": {"$ref": "#/definitions/nonNegativeInteger"},
        "minLength": {"$ref": "#/definitions/nonNegativeIntegerDefault0"},
        "pattern": {"type": "string", "format": "regex"},
        "additionalItems": {"$ref": "#"},
        "items": {"anyOf": [{"$ref": "#"}, {"$ref": "#/definitions/schemaArray"}], "default": True},
        "maxItems": {"$ref": "#/definitions/nonNegativeInteger"},
        "minItems": {"$ref": "#/definitions/nonNegativeIntegerDefault0"},
        "uniqueItems": {"type": "boolean", "default": False},
        "contains": {"$ref": "#"},
        "maxProperties": {"$ref": "#/definitions/nonNegativeInteger"},
        "minProperties": {"$ref": "#/definitions/nonNegativeIntegerDefault0"},
        "required": {"$ref": "#/definitions/stringArray"},
        "additionalProperties": {"$ref": "#"},
        "definitions": {"type": "object", "additionalProperties": {"$ref": "#"}, "default": {}},
        "properties": {"type": "object", "additionalProperties": {"$ref": "#"}, "default": {}},
        "patternProperties": {
            "type": "object",
            "additionalProperties": {"$ref": "#"},
            "propertyNames": {"format": "regex"},
            "default": {},
        },
        "dependencies": {
            "type": "object",
            "additionalProperties": {"anyOf": [{"$ref": "#"}, {"$ref": "#/definitions/stringArray"}]},
        },
        "propertyNames": {"$ref": "#"},
        "const": True,
        "enum": {"type": "array", "items": True, "minItems": 1, "uniqueItems": True},
        "type": {
            "anyOf": [
                {"$ref": "#/definitions/simpleTypes"},
                {"type": "array", "items": {"$ref": "#/definitions/simpleTypes"}, "minItems": 1, "uniqueItems": True},
            ]
        },
        "format": {"type": "string"},
        "contentMediaType": {"type": "string"},
        "contentEncoding": {"type": "string"},
        "if": {"$ref": "#"},
        "then": {"$ref": "#"},
        "else": {"$ref": "#"},
        "allOf": {"$ref": "#/definitions/schemaArray"},
        "anyOf": {"$ref": "#/definitions/schemaArray"},
        "oneOf": {"$ref": "#/definitions/schemaArray"},
        "not": {"$ref": "#"},
    },
    "default": True,
}
