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
from typing import Dict, Optional

from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate

from apigateway.utils.yaml import yaml_loads

from .plugin_checkers import PluginConfigYamlChecker
from .plugin_convertors import PluginConvertorFactory


class PluginConfigYamlValidator:
    """
    插件配置校验
    - 1. 符合 schema 规则
    - 2. 符合 apisix 额外校验规则 (plugin_checkers 中规则)
    """

    def validate(self, plugin_type_code: str, payload: str, schema: Optional[Dict] = None):
        """
        :param plugin_type_code: 插件类型
        :param payload: 插件 yaml 格式配置字符串
        :param schema: 插件 schema 规则
        """
        # 校验 schema 规则
        if schema:
            convertor = PluginConvertorFactory.get_convertor(plugin_type_code)
            try:
                validate(convertor.convert(yaml_loads(payload)), schema=schema)
            except JsonSchemaValidationError as err:
                raise ValueError(f"{err.message}, path {list(err.absolute_path)}")

        # 校验 apisix 额外规则
        checker = PluginConfigYamlChecker(plugin_type_code)
        checker.check(payload)
