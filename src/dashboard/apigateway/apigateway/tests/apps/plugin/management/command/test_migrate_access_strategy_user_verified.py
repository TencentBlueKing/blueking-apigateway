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
import json

import pytest
from ddf import G

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.management.commands.migrate_access_strategy_user_verified import (
    Command,
    init_app_plugin_config,
    init_stage_app_code_plugin_config,
    merge_plugin_config,
)
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.core.models import Gateway, Resource, Stage

pytestmark = pytest.mark.django_db


class TestBaseFunctions:
    def test_init_stage_app_code_plugin_config_one_stage_no_bindings(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway)
        c = init_stage_app_code_plugin_config(fake_gateway)

        assert c == {s1.id: {}}

    def test_init_stage_app_code_plugin_config_one_stage_one_binding_empty(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway)

        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": []}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        c = init_stage_app_code_plugin_config(fake_gateway)

        assert c == {s1.id: {}}

    def test_init_stage_app_code_plugin_config_one_stage_one_binding(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway)

        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        c = init_stage_app_code_plugin_config(fake_gateway)

        assert c == {
            s1.id: {
                "app_123": {
                    "bk_app_code": "app_123",
                    "dimension": "api",
                    "resource_ids": [],
                },
                "app_456": {
                    "bk_app_code": "app_456",
                    "dimension": "api",
                    "resource_ids": [],
                },
            }
        }

    def test_init_stage_app_code_plugin_config_two_stage_one_binding(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway)
        s2 = G(Stage, gateway=fake_gateway)

        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        c = init_stage_app_code_plugin_config(fake_gateway)

        assert c == {
            s1.id: {
                "app_123": {
                    "bk_app_code": "app_123",
                    "dimension": "api",
                    "resource_ids": [],
                },
                "app_456": {
                    "bk_app_code": "app_456",
                    "dimension": "api",
                    "resource_ids": [],
                },
            },
            s2.id: {},
        }

    def test_init_stage_app_code_plugin_config_three_stage_two_binding(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway)
        s2 = G(Stage, gateway=fake_gateway)
        s3 = G(Stage, gateway=fake_gateway)

        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        a2 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_456", "app_789"]}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s2.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a2,
        )

        c = init_stage_app_code_plugin_config(fake_gateway)

        assert c == {
            s1.id: {
                "app_123": {
                    "bk_app_code": "app_123",
                    "dimension": "api",
                    "resource_ids": [],
                },
                "app_456": {
                    "bk_app_code": "app_456",
                    "dimension": "api",
                    "resource_ids": [],
                },
            },
            s2.id: {
                "app_456": {
                    "bk_app_code": "app_456",
                    "dimension": "api",
                    "resource_ids": [],
                },
                "app_789": {
                    "bk_app_code": "app_789",
                    "dimension": "api",
                    "resource_ids": [],
                },
            },
            s3.id: {},
        }

    def test_init_app_plugin_config_empty(self, fake_gateway):
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": []}),
        )
        r1 = G(Resource, gateway=fake_gateway)
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )
        c = init_app_plugin_config(fake_gateway)

        assert c == {}

    def test_init_app_plugin_config_one_resource_one_access_strategy(self, fake_gateway):
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        r1 = G(Resource, gateway=fake_gateway)
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )
        c = init_app_plugin_config(fake_gateway)

        assert c == {
            "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [r1.id]},
            "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [r1.id]},
        }

    def test_init_app_plugin_config_two_resource_one_access_strategy(self, fake_gateway):
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        r1 = G(Resource, gateway=fake_gateway)
        r2 = G(Resource, gateway=fake_gateway)
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r2.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )
        c = init_app_plugin_config(fake_gateway)

        assert c == {
            "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [r1.id, r2.id]},
            "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [r1.id, r2.id]},
        }

    def test_init_app_plugin_config_two_resource_two_access_strategy(self, fake_gateway):
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        r1 = G(Resource, gateway=fake_gateway)
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        a2 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_456", "app_789"]}),
        )
        r2 = G(Resource, gateway=fake_gateway)
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r2.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a2,
        )
        c = init_app_plugin_config(fake_gateway)

        assert c == {
            "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [r1.id]},
            "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [r1.id, r2.id]},
            "app_789": {"bk_app_code": "app_789", "dimension": "resource", "resource_ids": [r2.id]},
        }

    @pytest.mark.parametrize(
        "stage_app_code_plugin_config, app_code_plugin_config, expected",
        [
            # 上游确保了 stage_app_code_plugin_config 一定非空
            ({123: {}}, {}, {123: {}}),
            (
                {123: {}},
                {"app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1, 2, 3]}},
                {123: {"app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1, 2, 3]}}},
            ),
            (
                {123: {"app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}}},
                {},
                {123: {"app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}}},
            ),
            # 都有值，app_code 不冲突
            (
                {123: {"app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}}},
                {"app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1, 2, 3]}},
                {
                    123: {
                        "app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []},
                        "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1, 2, 3]},
                    }
                },
            ),
            # 都有值，app_code 冲突，合并
            (
                {123: {"app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}}},
                {
                    "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [1, 2, 3]},
                    "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [4, 5, 6]},
                },
                {
                    123: {
                        "app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []},
                        "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [4, 5, 6]},
                    }
                },
            ),
            # 两个 stage，app_code 冲突，合并
            (
                {123: {"app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}}, 456: {}},
                {
                    "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [1, 2, 3]},
                    "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [4, 5, 6]},
                },
                {
                    123: {
                        "app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []},
                        "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [4, 5, 6]},
                    },
                    456: {
                        "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [1, 2, 3]},
                        "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [4, 5, 6]},
                    },
                },
            ),
        ],
    )
    def test_merged_plugin_config(self, stage_app_code_plugin_config, app_code_plugin_config, expected):
        assert merge_plugin_config(stage_app_code_plugin_config, app_code_plugin_config) == expected


class TestCommand:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        G(PluginType, code="bk-verified-user-exempted-apps")

    def test_handle_no_access_strategy(self, mocker, faker):
        command = Command()
        fake_gateway = G(Gateway)
        command.handle()

        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 0
        assert PluginConfig.objects.filter(gateway=fake_gateway).count() == 0

    def test_handle_only_stage_access_strategy_empty(self, mocker, faker):
        command = Command()
        fake_gateway = G(Gateway)

        s1 = G(Stage, gateway=fake_gateway)
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": []}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        command.handle()
        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 0
        assert PluginConfig.objects.filter(gateway=fake_gateway).count() == 0

    def test_handle_only_stage_access_strategy(self, mocker, faker):
        command = Command()
        fake_gateway = G(Gateway)

        s1 = G(Stage, gateway=fake_gateway)
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        s2 = G(Stage, gateway=fake_gateway)

        command.handle()

        plugin_type = PluginType.objects.get(code="bk-verified-user-exempted-apps")
        assert (
            PluginBinding.objects.filter(
                gateway=fake_gateway,
                scope_type=PluginBindingScopeEnum.STAGE.value,
                scope_id=s1.id,
                config__type=plugin_type,
            ).count()
            == 1
        )
        assert (
            PluginBinding.objects.filter(
                gateway=fake_gateway,
                scope_type=PluginBindingScopeEnum.STAGE.value,
                scope_id=s2.id,
                config__type=plugin_type,
            ).count()
            == 0
        )
        b = PluginBinding.objects.filter(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_id=s1.id,
            config__type=plugin_type,
        ).first()
        assert b.config.config == {
            "exempted_apps": [
                {
                    "bk_app_code": "app_123",
                    "dimension": "api",
                    "resource_ids": [],
                },
                {
                    "bk_app_code": "app_456",
                    "dimension": "api",
                    "resource_ids": [],
                },
            ]
        }

    def test_handle_all(self, mocker, faker):
        command = Command()
        fake_gateway = G(Gateway)

        s1 = G(Stage, gateway=fake_gateway)
        a1 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_123", "app_456"]}),
        )
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=s1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a1,
        )

        s2 = G(Stage, gateway=fake_gateway)

        a2 = G(
            AccessStrategy,
            api=fake_gateway,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            _config=json.dumps({"bk_app_code_list": ["app_456", "app_789"]}),
        )
        r1 = G(Resource, gateway=fake_gateway)
        G(
            AccessStrategyBinding,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_id=r1.id,
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            access_strategy=a2,
        )

        command.handle()

        plugin_type = PluginType.objects.get(code="bk-verified-user-exempted-apps")
        assert (
            PluginBinding.objects.filter(
                gateway=fake_gateway,
                scope_type=PluginBindingScopeEnum.STAGE.value,
                scope_id=s1.id,
                config__type=plugin_type,
            ).count()
            == 1
        )
        assert (
            PluginBinding.objects.filter(
                gateway=fake_gateway,
                scope_type=PluginBindingScopeEnum.STAGE.value,
                scope_id=s2.id,
                config__type=plugin_type,
            ).count()
            == 1
        )
        b1 = PluginBinding.objects.filter(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_id=s1.id,
            config__type=plugin_type,
        ).first()
        assert b1.config.config == {
            "exempted_apps": [
                {
                    "bk_app_code": "app_123",
                    "dimension": "api",
                    "resource_ids": [],
                },
                {
                    "bk_app_code": "app_456",
                    "dimension": "api",
                    "resource_ids": [],
                },
                {
                    "bk_app_code": "app_789",
                    "dimension": "resource",
                    "resource_ids": [r1.id],
                },
            ]
        }

        b2 = PluginBinding.objects.filter(
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_id=s2.id,
            config__type=plugin_type,
        ).first()
        assert b2.config.config == {
            "exempted_apps": [
                {
                    "bk_app_code": "app_456",
                    "dimension": "resource",
                    "resource_ids": [r1.id],
                },
                {
                    "bk_app_code": "app_789",
                    "dimension": "resource",
                    "resource_ids": [r1.id],
                },
            ]
        }
