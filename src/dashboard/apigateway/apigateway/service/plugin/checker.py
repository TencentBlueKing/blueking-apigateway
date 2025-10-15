# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
"""
插件数据校验器

- apisix 插件的 check_schema 校验失败，将导致绑定了插件的 API 无法访问
- apisix 插件的 check_schema 除校验 schema 外，可能还有一些额外的校验，这些插件配置的额外校验，放在此模块处理
"""

import ast
import ipaddress
import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import ClassVar, Dict, List, Optional

import jsonschema
from django.utils.translation import gettext as _

from apigateway.apps.plugin.constants import (
    Draft7Schema,
    PluginTypeCodeEnum,
)
from apigateway.utils.yaml import yaml_loads

from .normalizer import format_fault_injection_config

VARS_ALLOWED_COMPARISON_SYMBOLS = {"==", "~=", ">", ">=", "<", "<=", "~~", "~*", "in", "has", "!", "ipmatch"}


class BaseChecker(ABC):
    @abstractmethod
    def check(self, payload: str):
        pass


class BkCorsChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)

        self._check_allow_origins(loaded_data.get("allow_origins"))
        self._check_allow_origins_by_regex(loaded_data.get("allow_origins_by_regex"))
        self._check_allow_methods(loaded_data["allow_methods"])
        self._check_headers(loaded_data["allow_headers"], key="allow_headers")
        self._check_headers(loaded_data["expose_headers"], key="expose_headers")

        if loaded_data.get("allow_credential"):
            for key in ["allow_origins", "allow_methods", "allow_headers", "expose_headers"]:
                if loaded_data.get(key) == "*":
                    raise ValueError(_("当 'allow_credential' 为 True 时，{key} 不能为 '*'。").format(key=key))

        # 非 apisix check_schema 中逻辑，根据业务需要添加的校验逻辑
        if not (loaded_data.get("allow_origins") or loaded_data.get("allow_origins_by_regex")):
            raise ValueError(_("allow_origins, allow_origins_by_regex 不能同时为空。"))

        if loaded_data.get("allow_origins") and loaded_data.get("allow_origins_by_regex"):
            raise ValueError(_("allow_origins, allow_origins_by_regex 只能一个有效。"))

    def _check_allow_origins(self, allow_origins: Optional[str]):
        if not allow_origins:
            return
        self._check_duplicate_items(allow_origins.split(","), "allow_origins")

    def _check_allow_methods(self, allow_methods: str):
        self._check_duplicate_items(allow_methods.split(","), "allow_methods")

    def _check_headers(self, headers: str, key: str):
        self._check_duplicate_items(headers.split(","), key)

    def _check_allow_origins_by_regex(self, allow_origins_by_regex: List[str]):
        if not allow_origins_by_regex:
            return

        # 必须是一个合法的正则表达式
        for re_rule in allow_origins_by_regex:
            try:
                re.compile(re_rule)
            except Exception:  # pylint: disable=broad-except
                raise ValueError(
                    _("allow_origins_by_regex 中数据 '{re_rule}' 不是合法的正则表达式。").format(re_rule=re_rule)
                )

    def _check_duplicate_items(self, data: List[str], key: str):
        duplicate_items = [item for item, count in Counter(data).items() if count >= 2]
        if duplicate_items:
            raise ValueError(_("{} 存在重复的元素：{}。").format(key, ", ".join(duplicate_items)))


class HeaderRewriteChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)

        set_keys = [item["key"].lower() for item in loaded_data["set"]]
        set_duplicate_keys = [key for key, count in Counter(set_keys).items() if count >= 2]
        if set_duplicate_keys:
            raise ValueError(_("set 存在重复的元素：{}。").format(", ".join(set_duplicate_keys)))

        remove_keys = [item["key"] for item in loaded_data["remove"]]
        remove_duplicate_keys = [key for key, count in Counter(remove_keys).items() if count >= 2]
        if remove_duplicate_keys:
            raise ValueError(_("remove 存在重复的元素：{}。").format(", ".join(remove_duplicate_keys)))


class BkIPRestrictionChecker(BaseChecker):
    def _check_ip_content(self, ip_content: str):
        """check each line is a valid ipv4/ipv6 or ipv4 cidr/ipv6 cidr
        here we process line by line because we want to show the line number when raise error
        """
        ip_lines = ip_content.splitlines()

        for index, ip_line_raw in enumerate(ip_lines):
            ip_line = ip_line_raw.strip()
            # ignore empty line and comment line
            if not ip_line or ip_line.startswith("#"):
                continue

            try:
                ipaddress.ip_interface(ip_line)
            except Exception as e:  # pylint: disable=broad-except
                raise ValueError("line {}: {}".format(index + 1, e))

    def check(self, payload: str):
        """check the yaml payload is valid
        - yaml can not be empty
        - whitelist and blacklist can not be empty at the same time
        - each line of whitelist/blacklist is a valid ipv4/ipv6 or ipv4 cidr/ipv6 cidr(ignore empty line and comment)
        """

        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("yaml can not be empty")

        whitelist = loaded_data.get("whitelist")
        if whitelist:
            self._check_ip_content(whitelist)

        blacklist = loaded_data.get("blacklist")
        if blacklist:
            self._check_ip_content(blacklist)

        if not (whitelist or blacklist):
            raise ValueError("whitelist and blacklist can not be empty at the same time")


class RequestValidationChecker(BaseChecker):
    def _validate_json_schema(self, schema_name: str, json_schema: str):
        try:
            data = json.loads(json_schema)
        except json.JSONDecodeError:
            raise ValueError(f"Your {schema_name} Schema is not a valid JSON.")

        try:
            jsonschema.validate(instance=data, schema=Draft7Schema)
        except jsonschema.exceptions.ValidationError as err:
            raise ValueError(f"Your {schema_name} Schema is not valid: {err}")

        # FIXME: check the valid json schema

    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("yaml can not be empty")

        body_schema = loaded_data.get("body_schema")
        header_schema = loaded_data.get("header_schema")

        if not body_schema and not header_schema:
            raise ValueError("header_schema or body_schema should be configured at least one.")

        if body_schema:
            self._validate_json_schema("body_schema", body_schema)

        if header_schema:
            self._validate_json_schema("header_schema", header_schema)


class FaultInjectionChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        loaded_data = format_fault_injection_config(loaded_data)
        abort_data = loaded_data.get("abort")
        delay_data = loaded_data.get("delay")

        if not abort_data and not delay_data:
            raise ValueError("At least one of the conditions 'abort' or 'delay' must be configured.")

        if abort_data:
            http_status = abort_data.get("http_status")
            if not http_status:
                raise ValueError("http_status is required in abort.")
            if int(http_status) < 200:
                raise ValueError("http_status must be greater than 200.")

            percentage = abort_data.get("percentage")
            if percentage and not (0 < int(percentage) <= 100):
                raise ValueError("The percentage of abort must be greater than 0 and less than or equal to 100.")

            abort_vars = abort_data.get("vars")
            if abort_vars:
                check_vars(abort_vars, "abort")

        if delay_data:
            duration = delay_data.get("duration")
            if not duration:
                raise ValueError("duration is required in delay.")

            percentage = delay_data.get("percentage")
            if percentage and not (0 < int(percentage) <= 100):
                raise ValueError("The percentage of delay must be greater than 0 and less than or equal to 100.")

            delay_vars = delay_data.get("vars")
            if delay_vars:
                check_vars(delay_vars, "delay")


class ResponseRewriteChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        status_code = loaded_data.get("status_code")
        if status_code is not None and not (200 <= status_code <= 598):
            raise ValueError("status_code must be between 200 and 598.")

        response_rewrite_vars = loaded_data.get("vars")
        if response_rewrite_vars:
            check_vars(response_rewrite_vars, "response_rewrite")

        headers = loaded_data.get("headers")
        if headers:
            add_keys = [item["key"] for item in headers.get("add", [])]
            add_duplicate_keys = [key for key, count in Counter(add_keys).items() if count >= 2]
            if add_duplicate_keys:
                raise ValueError(_("add has duplicate elements：{}").format(", ".join(add_duplicate_keys)))

            set_keys = [item["key"].lower() for item in headers.get("set", [])]
            set_duplicate_keys = [key for key, count in Counter(set_keys).items() if count >= 2]
            if set_duplicate_keys:
                raise ValueError(_("set has duplicate elements：{}").format(", ".join(set_duplicate_keys)))

            remove_keys = [item["key"] for item in headers.get("remove", [])]
            remove_duplicate_keys = [key for key, count in Counter(remove_keys).items() if count >= 2]
            if remove_duplicate_keys:
                raise ValueError(_("remove has duplicate elements：{}").format(", ".join(remove_duplicate_keys)))


class RedirectChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        ret_code = loaded_data.get("ret_code")
        if ret_code is not None and not (ret_code >= 200):
            raise ValueError("ret_code must be greater than or equal to 200.")


class BkAccessTokenSourceChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        source = loaded_data.get("source")
        if source not in ["bearer", "api_key"]:
            raise ValueError("source must be bearer or api_key.")


class BKRequestBodyLimitChecker(BaseChecker):
    MAX_BODY_SIZE = 32 * 1024 * 1024  # 32MB

    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        max_body_size = loaded_data.get("max_body_size")
        if not (1 <= int(max_body_size) <= self.MAX_BODY_SIZE):
            raise ValueError("max_body_size must be between 1 byte and 32MB.")


class BKUserRestrictionChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        whitelist = loaded_data.get("whitelist", [])
        blacklist = loaded_data.get("blacklist", [])

        if whitelist:
            whitelist_keys = [item["key"] for item in whitelist]
            whitelist_duplicate_keys = [key for key, count in Counter(whitelist_keys).items() if count >= 2]
            if whitelist_duplicate_keys:
                raise ValueError(_("whitelist has duplicate elements：{}").format(", ".join(whitelist_duplicate_keys)))

        if blacklist:
            blacklist_keys = [item["key"] for item in blacklist]
            blacklist_duplicate_keys = [key for key, count in Counter(blacklist_keys).items() if count >= 2]
            if blacklist_duplicate_keys:
                raise ValueError(_("blacklist has duplicate elements：{}").format(", ".join(blacklist_duplicate_keys)))

        if not (whitelist or blacklist):
            raise ValueError("whitelist and blacklist can not be empty at the same time")


class ProxyCacheChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")

        cache_methods = [item["key"] for item in loaded_data["cache_method"]]
        if not cache_methods:
            raise ValueError("cache_method can not be empty")
        cache_method_keys = [key for key, count in Counter(cache_methods).items() if count >= 2]
        if cache_method_keys:
            raise ValueError(_("cache_method has duplicate elements：{}。").format(", ".join(cache_method_keys)))
        for method in cache_methods:
            if method not in ["GET", "HEAD"]:
                raise ValueError("cache_method only supports GET and HEAD")

        cache_ttl = loaded_data.get("cache_ttl")
        if not (1 <= int(cache_ttl) <= 3600):
            raise ValueError("cache_ttl must be between 1 and 3600 seconds")


def check_vars(vars, location):
    """check vars of lua-resty-expr
    vars = `[
        [
            [ "arg_name","==","jack" ],
            [ "arg_age","==",18 ]
        ],
        [
            [ "arg_name2","==111","allen" ]
        ]
    ]`

    """
    parsed_vars = []
    try:
        parsed_vars = ast.literal_eval(vars)
    except Exception as e:  # pylint: disable=broad-except
        raise ValueError(f"The vars of {location} is not valid, error: {e}")

    # 第一层 parsed_vars = [ [a], [] ]
    if not isinstance(parsed_vars, list):
        raise TypeError(f"The vars of {location} should be list")

    for index, v in enumerate(parsed_vars):
        # 中间层  v = [a]
        if not isinstance(v, list):
            raise TypeError(f"The vars of {location} at index {index} should be list")

        for i, item in enumerate(v):
            # 最内侧 a  = [ "arg_name","==","jack" ]
            if isinstance(item, list):
                if len(item) != 3:
                    raise ValueError(f"The vars of {location} at index [{index}][{i}] should have 3 elements")
                if item[1] not in VARS_ALLOWED_COMPARISON_SYMBOLS:
                    raise ValueError(
                        f"The vars of {location} at index [{index}][{i}] should have a valid comparison symbol"
                    )
            else:
                raise TypeError(f"The vars of {location} at index [{index}][{i}] should be list")


class PluginConfigYamlChecker:
    type_code_to_checker: ClassVar[Dict[str, BaseChecker]] = {
        PluginTypeCodeEnum.BK_CORS.value: BkCorsChecker(),
        PluginTypeCodeEnum.BK_HEADER_REWRITE.value: HeaderRewriteChecker(),
        PluginTypeCodeEnum.BK_IP_RESTRICTION.value: BkIPRestrictionChecker(),
        PluginTypeCodeEnum.REQUEST_VALIDATION.value: RequestValidationChecker(),
        PluginTypeCodeEnum.FAULT_INJECTION.value: FaultInjectionChecker(),
        PluginTypeCodeEnum.RESPONSE_REWRITE.value: ResponseRewriteChecker(),
        PluginTypeCodeEnum.REDIRECT.value: RedirectChecker(),
        PluginTypeCodeEnum.BK_ACCESS_TOKEN_SOURCE.value: BkAccessTokenSourceChecker(),
        PluginTypeCodeEnum.BK_REQUEST_BODY_LIMIT.value: BKRequestBodyLimitChecker(),
        PluginTypeCodeEnum.BK_USER_RESTRICTION.value: BKUserRestrictionChecker(),
        PluginTypeCodeEnum.PROXY_CACHE.value: ProxyCacheChecker(),
    }

    def __init__(self, type_code: str):
        self.type_code = type_code

    def check(self, payload: str):
        checker = self.type_code_to_checker.get(self.type_code)
        if checker:
            checker.check(payload)
