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
"""
from typing import Any, ClassVar, Dict

from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.utils.yaml import yaml_dumps, yaml_loads


class BasePluginYamlConvertor:
    def to_internal_value(self, yaml_: str) -> str:
        return yaml_

    def to_representation(self, yaml_: str) -> str:
        return yaml_


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

    def to_internal_value(self, yaml_: str) -> str:
        loaded_data = yaml_loads(yaml_)

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

    def to_representation(self, yaml_: str) -> str:
        loaded_data = yaml_loads(yaml_)

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


class CorsYamlConvertor(BasePluginYamlConvertor):
    def to_internal_value(self, yaml_: str) -> str:
        loaded_data = yaml_loads(yaml_)

        # 前端表单不支持不设置字段值，为使数据满足 schema 校验条件，删除一些空数据

        # allow_origins 要求必须满足正则条件，不能为空字符串
        if not loaded_data.get("allow_origins"):
            loaded_data.pop("allow_origins", None)

        # allow_origins_by_regex 要求数组最小长度为 1
        if not loaded_data.get("allow_origins_by_regex"):
            loaded_data.pop("allow_origins_by_regex", None)

        return yaml_dumps(loaded_data)


class HeaderRewriteYamlConvertor(BasePluginYamlConvertor):
    """
    前端传入的数据样例
    set:
      - key: key1
        value: value1
    remove:
      - key: key2

    存储的数据样例
    set:
      key1: value1
    remove:
      - key2
    """

    def to_internal_value(self, yaml_: str) -> str:
        loaded_data = yaml_loads(yaml_)

        result: Dict[str, Any] = {"set": {}, "remove": []}
        for item in loaded_data["set"]:
            result["set"][item["key"]] = item["value"]

        for item in loaded_data["remove"]:
            result["remove"].append(item["key"])

        return yaml_dumps(result)

    def to_representation(self, yaml_: str) -> str:
        loaded_data = yaml_loads(yaml_)

        result: Dict[str, list] = {"set": [], "remove": []}
        for key, value in loaded_data["set"].items():
            result["set"].append({"key": key, "value": value})

        for key in loaded_data["remove"]:
            result["remove"].append({"key": key})

        return yaml_dumps(result)


class PluginConfigYamlConvertor:
    type_code_to_convertor: ClassVar[Dict[str, BasePluginYamlConvertor]] = {
        PluginTypeCodeEnum.BK_RATE_LIMIT.value: RateLimitYamlConvertor(),
        PluginTypeCodeEnum.BK_CORS.value: CorsYamlConvertor(),
        PluginTypeCodeEnum.BK_HEADER_REWRITE.value: HeaderRewriteYamlConvertor(),
    }

    def __init__(self, type_code: str):
        self.type_code = type_code

    def to_internal_value(self, yaml_: str) -> str:
        convertor = self.type_code_to_convertor.get(self.type_code)
        if not convertor:
            return yaml_
        return convertor.to_internal_value(yaml_)

    def to_representation(self, yaml_: str) -> str:
        convertor = self.type_code_to_convertor.get(self.type_code)
        if not convertor:
            return yaml_
        return convertor.to_representation(yaml_)
