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

from apigateway.apis.open.stage import serializers
from apigateway.common.contexts import StageProxyHTTPContext, StageRateLimitContext
from apigateway.core.models import Stage


class TestStageWithResourceVersionV1SLZ:
    @pytest.mark.parametrize(
        "stage_name, stage_release, expected",
        [
            (
                "prod",
                {},
                [
                    {
                        "name": "prod",
                        "resource_version": None,
                        "released": False,
                    }
                ],
            ),
            (
                "test",
                {
                    "resource_version": {
                        "title": "test",
                        "version": "1.0.1",
                    },
                },
                [
                    {
                        "name": "test",
                        "resource_version": {
                            "version": "1.0.1",
                        },
                        "released": True,
                    }
                ],
            ),
        ],
    )
    def test_to_representation(self, fake_stage, stage_name, stage_release, expected):
        fake_stage.name = stage_name
        slz = serializers.StageWithResourceVersionV1SLZ(
            [fake_stage],
            many=True,
            context={
                "stage_release": {
                    fake_stage.id: stage_release,
                }
            },
        )
        assert slz.data == expected


class TestStageSyncInputSLZ:
    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": "test-05",
                "description": "t2",
                "status": 1,
                "vars": {
                    "test": "test",
                },
                "proxy_http": {
                    "timeout": 30,
                    "upstreams": {
                        "loadbalance": "weighted-roundrobin",
                        "hosts": [
                            {
                                "host": "http://www.b.com",
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {
                        "set": {"k2": "v2"},
                    },
                },
                "rate_limit": {
                    "enabled": True,
                    "rate": {
                        "tokens": 200,
                        "period": 3600,
                    },
                },
            },
            {
                "name": "test-05",
                "description": "t2",
                "status": 1,
                "vars": {
                    "foo": "bar",
                },
                "proxy_http": {
                    "timeout": 30,
                    "upstreams": {
                        "loadbalance": "weighted-roundrobin",
                        "hosts": [
                            {
                                "host": "http://www.b.com",
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {
                        "set": {"k2": "v2"},
                    },
                },
            },
        ],
    )
    def test_update(self, mocker, data, fake_gateway, fake_request):
        mocker.patch(
            "apigateway.common.plugin.header_rewrite.HeaderRewriteConvertor.alter_plugin",
            return_value=True,
        )

        fake_request.gateway = fake_gateway

        stage = G(
            Stage,
            api=fake_gateway,
            name="test-03",
            status=0,
            description="t1",
            _vars=json.dumps({"test": "123"}),
        )

        slz = serializers.StageSyncInputSLZ(
            stage,
            data=data,
            context={
                "request": fake_request,
                "allow_var_not_exist": True,
            },
        )
        slz.is_valid(raise_exception=True)

        slz.save(status=1)

        stage = Stage.objects.get(api=fake_gateway, name="test-03")
        assert stage.status == 0
        assert stage.vars == data["vars"]
        assert StageProxyHTTPContext().get_config(stage.id) == data["proxy_http"]
        if data.get("rate_limit"):
            assert StageRateLimitContext().get_config(stage.id) == data["rate_limit"]
        else:
            assert not StageRateLimitContext().filter_contexts(scope_ids=[stage.id]).exists()
