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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import Gateway


class TestAlarmStrategy(TestCase):
    def test_notice_receivers(self):
        gateway = G(Gateway, _maintainers="test")
        strategy = G(
            AlarmStrategy,
            gateway=gateway,
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )

        data = [
            {
                "config": {
                    "detect_config": {"duration": 300, "method": "gte", "count": 10},
                    "converge_config": {"duration": 300},
                    "notice_config": {
                        "notice_way": [
                            "wechat",
                        ],
                        "notice_role": ["maintainer"],
                        "notice_extra_receiver": ["admin"],
                    },
                },
                "expected": ["admin", "test"],
            },
            {
                "config": {
                    "detect_config": {"duration": 300, "method": "gte", "count": 10},
                    "converge_config": {"duration": 300},
                    "notice_config": {
                        "notice_way": [
                            "wechat",
                        ],
                        "notice_role": [],
                        "notice_extra_receiver": [
                            "admin",
                            "admin",
                        ],
                    },
                },
                "expected": ["admin"],
            },
            {
                "config": {
                    "detect_config": {"duration": 300, "method": "gte", "count": 10},
                    "converge_config": {"duration": 300},
                    "notice_config": {
                        "notice_way": [
                            "wechat",
                        ],
                        "notice_role": [
                            "maintainer",
                        ],
                        "notice_extra_receiver": [],
                    },
                },
                "expected": ["test"],
            },
        ]
        for test in data:
            strategy.config = test["config"]
            self.assertEqual(sorted(strategy.notice_receivers), test["expected"], test["config"])

    def test_effective_stages_getter(self):
        gateway = G(Gateway)
        strategy = G(
            AlarmStrategy,
            gateway=gateway,
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )

        # Test empty stages
        strategy._effective_stages = ""
        self.assertEqual(strategy.effective_stages, [])

        # Test single stage
        strategy._effective_stages = "prod"
        self.assertEqual(strategy.effective_stages, ["prod"])

        # Test multiple stages
        strategy._effective_stages = "prod,test,dev"
        self.assertEqual(strategy.effective_stages, ["prod", "test", "dev"])

    def test_effective_stages_setter(self):
        gateway = G(Gateway)
        strategy = G(
            AlarmStrategy,
            gateway=gateway,
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )

        # Test empty stages
        strategy.effective_stages = []
        self.assertEqual(strategy._effective_stages, "")

        # Test single stage
        strategy.effective_stages = ["prod"]
        self.assertEqual(strategy._effective_stages, "prod")

        # Test multiple stages
        strategy.effective_stages = ["prod", "test", "dev"]
        self.assertEqual(strategy._effective_stages, "prod,test,dev")

    def test_is_effective_stage(self):
        gateway = G(Gateway)
        strategy = G(
            AlarmStrategy,
            gateway=gateway,
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )

        # Test empty stage
        self.assertFalse(strategy.is_effective_stage(""))

        # Test when all stages are effective
        strategy._effective_stages = ""
        self.assertTrue(strategy.is_effective_stage("prod"))
        self.assertTrue(strategy.is_effective_stage("test"))
        self.assertTrue(strategy.is_effective_stage("dev"))

        # Test specific stages
        strategy._effective_stages = "prod,test"
        self.assertTrue(strategy.is_effective_stage("prod"))
        self.assertTrue(strategy.is_effective_stage("test"))
        self.assertFalse(strategy.is_effective_stage("dev"))
