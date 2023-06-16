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
import re
from typing import ClassVar, Dict

from django.utils.translation import gettext as _

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.utils.yaml import yaml_loads


class BaseChecker:
    def check(self, yaml_: str):
        pass


class BkCorsChecker(BaseChecker):
    def check(self, yaml_: str):
        loaded_data = yaml_loads(yaml_)

        if loaded_data.get("allow_credential"):
            for key in ["allow_origins", "allow_methods", "allow_headers", "expose_headers"]:
                if loaded_data.get(key) == "*":
                    raise ValueError(_("当 'allow_credential' 为 True 时, {key} 不能为 '*'。").format(key=key))

        if loaded_data.get("allow_origins_by_regex"):
            for re_rule in loaded_data["allow_origins_by_regex"]:
                try:
                    re.compile(re_rule)
                except Exception:
                    raise ValueError(_("allow_origins_by_regex 中数据 '{re_rule}' 不是合法的正则表达式。").format(re_rule=re_rule))

        # 非 apisix check_schema 中逻辑，根据业务需要添加的校验逻辑
        if not (loaded_data.get("allow_origins") or loaded_data.get("allow_origins_by_regex")):
            raise ValueError(_("allow_origins, allow_origins_by_regex 不能同时为空。"))


class PluginConfigYamlChecker:
    type_code_to_checker: ClassVar[Dict[str, BaseChecker]] = {
        PluginTypeCodeEnum.BK_CORS.value: BkCorsChecker(),
    }

    def __init__(self, type_code: str):
        self.type_code = type_code

    def check(self, yaml_: str):
        checker = self.type_code_to_checker.get(self.type_code)
        if checker:
            checker.check(yaml_)
