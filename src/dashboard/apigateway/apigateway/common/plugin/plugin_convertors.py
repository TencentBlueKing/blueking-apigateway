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

# PluginConfig 中前端表单数据，转换成 apisix 插件配置

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Union

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.utils.ip import parse_ip_content_to_list


class PluginConvertor(ABC):
    plugin_type_code: ClassVar[PluginTypeCodeEnum]

    @abstractmethod
    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        pass


class DefaultPluginConvertor(PluginConvertor):
    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """convert to apisix plugin config
        default is the PluginConfig.config(`yaml.loads(yaml_)`)

        if need covert, overwrite this method
        """
        return config


class HeaderWriteConvertor(PluginConvertor):
    plugin_type_code: ClassVar[PluginTypeCodeEnum] = PluginTypeCodeEnum.BK_HEADER_REWRITE

    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "set": {item["key"]: item["value"] for item in config["set"]},
            "remove": [item["key"] for item in config["remove"]],
        }


class IPRestrictionConvertor(PluginConvertor):
    plugin_type_code: ClassVar[PluginTypeCodeEnum] = PluginTypeCodeEnum.BK_IP_RESTRICTION

    def _parse_config_to_ips(self, item: Union[str, list]) -> List[str]:
        if isinstance(item, str):
            return parse_ip_content_to_list(item)

        # legacy data
        if isinstance(item, list):
            # deduplicate
            return list(set(item))
        return None

    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """generate config for bk-ip-restriction
        note: either one of whitelist or blacklist attribute must be specified. They cannot be used together!
        """
        whitelist = []
        # here we need to compatible with old version data, the item is ip or ip_content
        whitelist_data = config.get("whitelist")
        if whitelist_data:
            whitelist = self._parse_config_to_ips(whitelist_data)
            return {"whitelist": whitelist}

        blacklist = []
        blacklist_data = config.get("blacklist")
        if blacklist_data:
            blacklist = self._parse_config_to_ips(blacklist_data)
            return {"blacklist": blacklist}

        # the config from frontend is wrong!
        raise ValueError("either one of whitelist or blacklist attribute must be specified for bk-ip-restriction")


class BkCorsConvertor(PluginConvertor):
    plugin_type_code: ClassVar[PluginTypeCodeEnum] = PluginTypeCodeEnum.BK_CORS

    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # allow_origins 要求必须满足正则条件，不能为空字符串，且其不存在时，在 apisix 默认值为 *，
        # 若 allow_credential=true，apisix schema 校验会失败，因此为空时，将其设置为 "null"
        config["allow_origins"] = config.get("allow_origins") or "null"

        # allow_origins_by_regex 要求数组最小长度为 1
        if not config.get("allow_origins_by_regex"):
            config.pop("allow_origins_by_regex", None)

        return config


class BkMockConvertor(PluginConvertor):
    plugin_type_code: ClassVar[PluginTypeCodeEnum] = PluginTypeCodeEnum.BK_MOCK

    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        config["response_headers"] = {item["key"]: item["value"] for item in config["response_headers"]}
        return config


class PluginConvertorFactory:
    plugin_convertors: ClassVar[Dict[PluginTypeCodeEnum, PluginConvertor]] = {
        c.plugin_type_code: c
        for c in [
            HeaderWriteConvertor(),
            IPRestrictionConvertor(),
            BkCorsConvertor(),
            BkMockConvertor(),
        ]
    }

    @classmethod
    def get_convertor(cls, plugin_type_code: str) -> PluginConvertor:
        return cls.plugin_convertors.get(PluginTypeCodeEnum(plugin_type_code), DefaultPluginConvertor())
