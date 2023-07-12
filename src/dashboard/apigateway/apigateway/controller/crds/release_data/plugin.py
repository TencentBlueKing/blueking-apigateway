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
from typing import Any, ClassVar, Dict

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginConfig


class PluginConvertor(ABC):
    plugin_type_code: ClassVar[str]

    @abstractmethod
    def convert(self, plugin_config: PluginConfig) -> Dict[str, Any]:
        pass


class DefaultPluginConvertor(PluginConvertor):
    def convert(self, plugin_config: PluginConfig) -> Dict[str, Any]:
        """convert to apisix plugin config
        default is the PluginConfig.config(`yaml.loads(yaml_)`)
        if need covert, overwrite this method
        """
        return plugin_config.config


class HeaderWriteConvertor(PluginConvertor):
    plugin_type_code: ClassVar[str] = PluginTypeCodeEnum.BK_HEADER_REWRITE.value

    def convert(self, plugin_config: PluginConfig) -> Dict[str, Any]:
        config = plugin_config.config

        return {
            "set": {item["key"]: item["value"] for item in config["set"]},
            "remove": [item["key"] for item in config["remove"]],
        }


class PluginConvertorFactory:
    plugin_convertors: ClassVar[Dict[PluginTypeCodeEnum, PluginConvertor]] = {
        c.plugin_type_code: c  # type: ignore
        for c in [
            HeaderWriteConvertor(),
        ]
    }

    @classmethod
    def get_convertor(cls, plugin_type_code: PluginTypeCodeEnum) -> PluginConvertor:
        return cls.plugin_convertors.get(plugin_type_code, DefaultPluginConvertor())
