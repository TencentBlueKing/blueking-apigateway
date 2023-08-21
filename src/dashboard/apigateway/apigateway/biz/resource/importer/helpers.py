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
import pkgutil


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


def format_jsonschema_error(error):
    return f"{format_as_index(error.absolute_path)}: {error.message}"


class AuthConfigConverter:
    """
    资源认证配置，Yaml 与内部数据的转换
    """

    @classmethod
    def to_yaml(cls, auth_config: dict):
        _config = {
            "userVerifiedRequired": auth_config.get("auth_verified_required", True),
        }

        if auth_config.get("app_verified_required") is False:
            _config["appVerifiedRequired"] = False

        if auth_config.get("resource_perm_required") is False:
            _config["resourcePermissionRequired"] = False

        return _config

    @classmethod
    def to_inner(cls, auth_config: dict):
        _config = {
            "auth_verified_required": auth_config.get("userVerifiedRequired", True),
        }

        if "appVerifiedRequired" in auth_config:
            _config["app_verified_required"] = auth_config["appVerifiedRequired"]

        if "resourcePermissionRequired" in auth_config:
            _config["resource_perm_required"] = auth_config["resourcePermissionRequired"]

        return _config
