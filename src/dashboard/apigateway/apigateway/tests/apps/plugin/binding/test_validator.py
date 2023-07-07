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

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.plugin.binding.validator import PluginBindingValidator
from apigateway.apps.plugin.constants import PluginBindingScopeEnum


class TestPluginBindingValidator:
    def test_validate(self, fake_gateway, fake_stage, rate_limit_access_strategy_stage_binding):
        validator = PluginBindingValidator(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_ids=[fake_stage.id],
            plugin_type_code="bk-ip-restriction",
        )
        assert validator.validate() is None

        validator = PluginBindingValidator(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_ids=[fake_stage.id],
            plugin_type_code="bk-cors",
        )
        assert validator.validate() is None

        validator = PluginBindingValidator(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_ids=[fake_stage.id],
            plugin_type_code="bk-rate-limit",
        )
        with pytest.raises(ValueError):
            validator.validate()

    @pytest.mark.parametrize(
        "type_code, strategy_type",
        [
            ("bk-rate-limit", "rate_limit"),
            ("bk-verified-user-exempted-apps", "user_verified_unrequired_apps"),
            ("bk-status-rewrite", "error_status_code_200"),
            ("bk-cors", "cors"),
            ("bk-ip-restriction", "ip_access_control"),
        ],
    )
    def test_get_access_strategy_type(self, fake_gateway, type_code, strategy_type):
        validator = PluginBindingValidator(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_ids=[1],
            plugin_type_code="foo",
        )

        result = validator._get_access_strategy_type(type_code)
        assert result == (strategy_type and AccessStrategyTypeEnum(strategy_type))
