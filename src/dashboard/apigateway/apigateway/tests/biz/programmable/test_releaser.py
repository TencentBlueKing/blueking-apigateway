#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import datetime

import pytest
from ddf import G

from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.programmable import ProgrammableGatewayReleaser
from apigateway.core.models import Gateway, Stage
from apigateway.tests.utils.testing import dummy_time

pytestmark = pytest.mark.django_db


class TestProgrammableGatewayReleaser:
    def test_filter_deploy_history(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, gateway=gateway, name="prod")
        stage_test = G(Stage, gateway=gateway, name="test")

        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage_prod, version="1.0.0")
        G(
            ProgrammableGatewayDeployHistory,
            gateway=gateway,
            stage=stage_prod,
            version="1.0.1",
            created_by="admin",
        )
        G(
            ProgrammableGatewayDeployHistory,
            gateway=gateway,
            stage=stage_prod,
            version="1.0.2",
            created_time=dummy_time.time,
        )
        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage_test, version="2.0.0")

        data = [
            {
                "params": {
                    "query": "prod",
                },
                "expected": {
                    "count": 3,
                },
            },
            {
                "params": {
                    "stage_id": stage_prod.id,
                },
                "expected": {
                    "count": 3,
                },
            },
            {
                "params": {
                    "created_by": "adm",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "created_by": "adm",
                },
                "fuzzy": False,
                "expected": {
                    "count": 0,
                },
            },
            {
                "params": {
                    "created_by": "admin",
                },
                "fuzzy": False,
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "query": "prod",
                },
                "fuzzy": False,
                "expected": {
                    "count": 4,
                },
            },
            {
                "params": {
                    "time_start": dummy_time.time - datetime.timedelta(hours=1),
                    "time_end": dummy_time.time + datetime.timedelta(hours=1),
                },
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            result = ProgrammableGatewayReleaser.filter_deploy_history(
                gateway, fuzzy=test.get("fuzzy", True), **test["params"]
            )
            assert result.count() == test["expected"]["count"]
