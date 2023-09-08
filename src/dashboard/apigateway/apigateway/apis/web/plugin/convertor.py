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
插件数据转换器

- 前端插件表单和后端存储的数据，可能不一致，需要自定义转换逻辑
- 尽量使用插件表单的数据，减少不必要的转换

-------------------

为了更好的支持插件表单的编辑和展示，前端产生的数据直接存储，不做任何转换; apisix 使用的配置单独在发布时做处理

NOTE:
1. 新插件尽量不写 convertor, 直接保存表单的数据，在 转换成 apisix 配置的时候，进行转换 (以确保编辑态的数据顺序和内容)
2. 存量已经编写了 convertor 的插件暂时不动
"""
from typing import ClassVar, Dict

from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.utils.yaml import yaml_dumps, yaml_loads


class BasePluginYamlConvertor:
    def to_internal_value(self, payload: str) -> str:
        return payload

    def to_representation(self, payload: str) -> str:
        return payload


class RateLimitYamlConvertor(BasePluginYamlConvertor):
    """
    前端传入的数据样例
    rates:
      default:
        period: 1
        tokens: 1
      specials:
        - period: 1
          bk_app_code: test
          tokens: 10

    存储的数据样例
    rates:
      __default:
        - period: 1
          tokens: 1
      test:
        - period: 1
          tokens: 10
    """

    def to_internal_value(self, payload: str) -> str:
        loaded_data = yaml_loads(payload)

        result: Dict[str, dict] = {"rates": {}}
        # 特殊应用频率
        for item in loaded_data["rates"].get("specials", []):
            bk_app_code = item["bk_app_code"]
            if bk_app_code in result["rates"]:
                raise ValidationError({"bk_app_code": _(f"蓝鲸应用ID重复: {bk_app_code}").format(bk_app_code=bk_app_code)})

            result["rates"][bk_app_code] = [{"period": item["period"], "tokens": item["tokens"]}]

        # 蓝鲸应用默认频率
        default_rate = loaded_data["rates"]["default"]
        result["rates"]["__default"] = [{"period": default_rate["period"], "tokens": default_rate["tokens"]}]

        return yaml_dumps(result)

    def to_representation(self, payload: str) -> str:
        loaded_data = yaml_loads(payload)

        result: Dict[str, dict] = {"rates": {"default": {}, "specials": []}}
        for bk_app_code, rates in loaded_data["rates"].items():
            # 目前仅支持单个频率配置
            rate = rates[0]

            if bk_app_code == "__default":
                result["rates"]["default"] = {"period": rate["period"], "tokens": rate["tokens"]}
            else:
                result["rates"]["specials"].append(
                    {
                        "period": rate["period"],
                        "tokens": rate["tokens"],
                        "bk_app_code": bk_app_code,
                    }
                )

        return yaml_dumps(result)


class IPRestrictionYamlConvertor(BasePluginYamlConvertor):
    def to_representation(self, payload: str) -> str:
        """this is a compatibility method, for old data, convert to new format"""
        if payload.startswith(("whitelist: |-", "blacklist: |-")):
            return payload

        # old: whitelist:\n  - 1.1.1.1\n  - 2.2.2.2\n  - 1.1.1.1/24
        # new: whitelist: |-\n  127.0.0.1\n\n  1.1.1.1\n\n  # abcde\n\n  2.2.2.2\n\n  3.3.3.3
        if payload.startswith("whitelist:") and (not payload.startswith("whitelist: |-")):
            return payload.replace("- ", "").replace("whitelist:", "whitelist: |-")

        if payload.startswith("blacklist:") and (not payload.startswith("blacklist: |-")):
            return payload.replace("- ", "").replace("blacklist:", "blacklist: |-")

        return payload


class PluginConfigYamlConvertor:
    type_code_to_convertor: ClassVar[Dict[str, BasePluginYamlConvertor]] = {
        PluginTypeCodeEnum.BK_RATE_LIMIT.value: RateLimitYamlConvertor(),
        PluginTypeCodeEnum.BK_IP_RESTRICTION.value: IPRestrictionYamlConvertor(),
    }

    def __init__(self, type_code: str):
        self.type_code = type_code

    def to_internal_value(self, payload: str) -> str:
        convertor = self.type_code_to_convertor.get(self.type_code)
        if not convertor:
            return payload
        return convertor.to_internal_value(payload)

    def to_representation(self, payload: str) -> str:
        convertor = self.type_code_to_convertor.get(self.type_code)
        if not convertor:
            return payload
        return convertor.to_representation(payload)
