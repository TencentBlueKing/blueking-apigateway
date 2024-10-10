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
import pytest

from apigateway.common.plugin.validator import PluginConfigYamlValidator
from apigateway.utils.yaml import yaml_dumps


class TestPluginConfigYamlValidator:
    def test_validate(self, mocker, fake_plugin_bk_header_rewrite, fake_plugin_type_bk_header_rewrite_schema):
        validator = PluginConfigYamlValidator()

        validator.validate(
            "bk-header-rewrite",
            yaml_dumps({"set": [{"key": "foo", "value": "bar"}], "remove": []}),
            fake_plugin_type_bk_header_rewrite_schema.schema,
        )
        validator.validate("bk-header-rewrite", yaml_dumps({"set": [], "remove": [{"key": "foo:bar"}]}), None)

        with pytest.raises(ValueError):
            validator.validate(
                "bk-header-rewrite",
                yaml_dumps({"set": [], "remove": [{"key": "foo:bar"}]}),
                fake_plugin_type_bk_header_rewrite_schema.schema,
            )

        mocker.patch(
            "apigateway.common.plugin.validator.PluginConfigYamlChecker.check",
            side_effect=ValueError(),
        )
        with pytest.raises(ValueError):
            validator.validate("bk-header-rewrite", yaml_dumps({"set": [], "remove": [{"key": "foo:bar"}]}), None)
