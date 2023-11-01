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
"""
插件数据校验器

- apisix 插件的 check_schema 校验失败，将导致绑定了插件的 API 无法访问
- apisix 插件的 check_schema 除校验 schema 外，可能还有一些额外的校验，这些插件配置的额外校验，放在此模块处理
"""
import ipaddress
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import ClassVar, Dict, List, Optional

from django.utils.translation import gettext as _

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.utils.yaml import yaml_loads


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
                    raise ValueError(_("当 'allow_credential' 为 True 时, {key} 不能为 '*'。").format(key=key))

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
            except Exception:
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

        set_keys = [item["key"] for item in loaded_data["set"]]
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
            except Exception as e:
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


class PluginConfigYamlChecker:
    type_code_to_checker: ClassVar[Dict[str, BaseChecker]] = {
        PluginTypeCodeEnum.BK_CORS.value: BkCorsChecker(),
        PluginTypeCodeEnum.BK_HEADER_REWRITE.value: HeaderRewriteChecker(),
        PluginTypeCodeEnum.BK_IP_RESTRICTION.value: BkIPRestrictionChecker(),
    }

    def __init__(self, type_code: str):
        self.type_code = type_code

    def check(self, payload: str):
        checker = self.type_code_to_checker.get(self.type_code)
        if checker:
            checker.check(payload)
