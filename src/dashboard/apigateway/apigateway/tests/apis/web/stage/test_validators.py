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
import pytest
from ddf import G
from rest_framework import serializers

from apigateway.apis.web.stage.validators import StageVarsValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import Gateway, Release, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_request

pytestmark = pytest.mark.django_db


class TestStageVarsValidator:
    class StageSLZ(serializers.ModelSerializer):
        api = serializers.HiddenField(default=CurrentGatewayDefault())
        vars = serializers.DictField(label="环境变量", child=serializers.CharField())

        class Meta:
            model = Stage
            fields = (
                "api",
                "vars",
            )

            validators = [StageVarsValidator()]

    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway

    def test_validate_vars_keys(self):
        data = [
            {
                "params": {
                    # error, first is not char
                    "vars": {
                        "12345": "a",
                    },
                },
                "will_error": True,
            },
            {
                "params": {
                    # error, over length
                    "vars": {
                        "a" * 51: "a",
                    },
                },
                "will_error": True,
            },
            {
                "params": {
                    # error, include -
                    "vars": {
                        "abc-d": "a",
                    },
                },
                "will_error": True,
            },
            {
                "params": {
                    "vars": {
                        "domian_2": "a",
                    },
                },
                "will_error": False,
            },
            {
                "params": {
                    "vars": {
                        "a" * 50: "a",
                    },
                },
                "will_error": False,
            },
        ]
        for test in data:
            slz = self.StageSLZ(data=test["params"], context={"request": self.request})
            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors, test["params"]
            else:
                assert not slz.errors, test["params"]

    def test_validate_vars_values(self, mocker):
        stage = G(Stage, api=self.gateway, status=1)
        resource_version = G(ResourceVersion, gateway=self.gateway)
        G(Release, gateway=self.gateway, stage=stage, resource_version=resource_version)

        data = [
            # ok
            {
                "vars": {
                    "prefix": "/o",
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": False,
            },
            # var in path not exist
            {
                "vars": {
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            # var in path invalid
            {
                "vars": {
                    "prefix": "/test/?a=b",
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            # var in hosts not exist
            {
                "vars": {
                    "prefix": "/test/",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            # var in hosts invalid
            {
                "vars": {
                    "prefix": "/test/",
                    "domain": "http://bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
        ]
        for test in data:
            slz = self.StageSLZ(instance=stage, data={"vars": test["vars"]}, context={"request": self.request})
            mocker.patch(
                "apigateway.apis.web.stage.validators.ResourceVersion.objects.get_used_stage_vars",
                return_value=test["mock_used_stage_vars"],
            )

            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors
            else:
                assert not slz.errors
