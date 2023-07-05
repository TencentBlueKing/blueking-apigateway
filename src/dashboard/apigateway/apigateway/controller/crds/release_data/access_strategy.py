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

import re
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from attrs import define

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, IPGroup
from apigateway.controller.crds.release_data.base import PluginData
from apigateway.utils.header import canonical_header_key


@define(slots=False)
class AccessStrategyConvertor:
    """访问策略转换器，将访问策略转换为 PluginData"""

    access_strategy_type: ClassVar[AccessStrategyTypeEnum]
    plugin_type_code: ClassVar[str]

    def to_plugin_data(self, scope_type: AccessStrategyBindScopeEnum, access_strategy: AccessStrategy) -> PluginData:
        # here, the type_code is the new plugin name, config is the plugin config
        return PluginData(
            type_code=self.plugin_type_code,
            config=self._to_plugin_config(access_strategy),
            binding_scope_type=scope_type.value,
        )

    def _to_plugin_config(self, access_strategy: AccessStrategy) -> Dict[str, Any]:
        return access_strategy.config


class StatusCode200ASC(AccessStrategyConvertor):
    """网关错误使用 HTTP 状态码 200(不推荐)"""

    access_strategy_type: ClassVar[AccessStrategyTypeEnum] = AccessStrategyTypeEnum.ERROR_STATUS_CODE_200
    plugin_type_code: ClassVar[str] = "bk-status-rewrite"


class UserVerifiedUnrequiredAppsASC(AccessStrategyConvertor):
    """免用户认证应用白名单"""

    access_strategy_type: ClassVar[AccessStrategyTypeEnum] = AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS
    plugin_type_code: ClassVar[str] = "bk-verified-user-exempted-apps"

    def _to_plugin_config(self, access_strategy: AccessStrategy) -> Dict[str, List[Any]]:
        config = access_strategy.config or {}
        return {
            "exempted_apps": [
                {
                    "bk_app_code": app_code,
                    "dimension": "api",
                    "resource_ids": [],
                }
                for app_code in config.get("bk_app_code_list", [])
            ]
        }


class RateLimitASC(AccessStrategyConvertor):
    """频率控制"""

    access_strategy_type: ClassVar[AccessStrategyTypeEnum] = AccessStrategyTypeEnum.RATE_LIMIT
    plugin_type_code: ClassVar[str] = "bk-rate-limit"


class IpAccessControlASC(AccessStrategyConvertor):
    """IP 访问控制"""

    access_strategy_type: ClassVar[AccessStrategyTypeEnum] = AccessStrategyTypeEnum.IP_ACCESS_CONTROL
    plugin_type_code: ClassVar[str] = "bk-ip-restriction"

    def _parse_ip_content_list(self, ip_content_list: List[str]) -> List[str]:
        ips = set()
        for ip_content in ip_content_list:
            # split with \n\r, then ignore blank line and `# comment`
            ip_lines = re.split(r"[\n\r]+", ip_content)
            for ip_line in ip_lines:
                ip_line = ip_line.strip()
                if not ip_line or ip_line.startswith("#"):
                    continue
                ips.add(ip_line)

        # we are not going to do the merge now, we will do it in the future if that become a problem
        # TODO: merge by cidr
        return list(ips)

    def _to_plugin_config(self, access_strategy: AccessStrategy):
        """
        old data:
            allow: { content: group._ips } / deny: { content: group._ips }
            (group._ips is a text field, with empty lines, comments)
        convert to:
            whitelist: [] / blacklist: []
        """
        whitelist: List[str] = []
        blacklist: List[str] = []

        config = access_strategy.config
        ipContentList = [group._ips for group in IPGroup.objects.filter(id__in=config["ip_group_list"])]
        ip_list = self._parse_ip_content_list(ipContentList)

        # the access strategy will be remove soon, so use `allow` and `deny` here directly
        if config["type"] == "allow":
            whitelist = ip_list
        elif config["type"] == "deny":
            blacklist = ip_list
        # do nothing if type is wrong

        return {
            "whitelist": whitelist,
            "blacklist": blacklist,
        }


class CorsASC(AccessStrategyConvertor):
    """CORS"""

    access_strategy_type: ClassVar[AccessStrategyTypeEnum] = AccessStrategyTypeEnum.CORS
    plugin_type_code: ClassVar[str] = "bk-cors"

    def _to_plugin_config(self, access_strategy: AccessStrategy) -> Dict[str, Any]:
        """
        apisix cors 插件：https://github.com/apache/apisix/blob/master/apisix/plugins/cors.lua
        """
        config = access_strategy.config
        allow_origins, allow_origins_by_regex = self._convert_allowed_origins(config["allowed_origins"])
        plugin_config = {
            "allow_origins": allow_origins,
            "allow_methods": self._convert_allowed_methods(config["allowed_methods"]),
            "allow_headers": self._convert_allowed_headers(config["allowed_headers"]),
            "expose_headers": self._convert_expose_headers(config.get("exposed_headers", [])),
            "max_age": config.get("max_age", 5),
            "allow_credential": config.get("allow_credentials") or False,
        }
        if allow_origins_by_regex:
            plugin_config["allow_origins_by_regex"] = allow_origins_by_regex

        return plugin_config

    def _convert_allowed_origins(self, allowed_origins: List[str]) -> Tuple[str, Optional[List]]:
        allow_origins = []
        allow_origins_by_regex = []
        for origin in allowed_origins:
            if origin == "*":
                return "**", None

            elif "*" in origin:
                # 1. 域名中，可能已包含正则中的特殊字符，需转义，如 "."
                # 2. 域名中 * 表示任意字符，正则表达式中，需替换为".*"，如 http://*.example.com，需匹配 http://a.example.com, http://b.example.com
                # 3. 正则添加开头和结尾 "^$"，防止 http://a.example.com1 匹配到正则 "http://.*\.example\.com"
                origin_by_regex = "^{origin}$".format(
                    origin=origin.replace(".", r"\.")
                    .replace("-", r"\-")
                    .replace("[", r"\[")
                    .replace("]", r"\]")
                    .replace("*", ".*")
                )
                allow_origins_by_regex.append(origin_by_regex)

            else:
                allow_origins.append(origin)

        # allow_origins 不能为空字符串，未设置时将使用默认值 "*"，因此为空时将其设置为 null
        return ",".join(allow_origins) or "null", allow_origins_by_regex

    def _convert_allowed_methods(self, allowed_methods: List[str]) -> str:
        return ",".join(map(str.upper, allowed_methods))

    def _convert_allowed_headers(self, allowed_headers: List[str]) -> str:
        if "*" in allowed_headers:
            return "**"

        return ",".join(map(canonical_header_key, allowed_headers))

    def _convert_expose_headers(self, exposed_headers: List[str]) -> str:
        if "*" in exposed_headers:
            return "**"

        return ",".join(map(canonical_header_key, exposed_headers))


class AccessStrategyConvertorFactory:
    access_strategy_convertors: ClassVar[Dict[AccessStrategyTypeEnum, AccessStrategyConvertor]] = {
        c.access_strategy_type: c  # type: ignore
        for c in [
            StatusCode200ASC(),
            UserVerifiedUnrequiredAppsASC(),
            RateLimitASC(),
            IpAccessControlASC(),
            CorsASC(),
        ]
    }

    @classmethod
    def get_convertor(cls, access_strategy_type: AccessStrategyTypeEnum) -> Optional[AccessStrategyConvertor]:
        return cls.access_strategy_convertors.get(access_strategy_type)
