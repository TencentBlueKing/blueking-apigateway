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
from rest_framework.serializers import ValidationError

from apigateway.apps.micro_gateway.serializers import ListMicroGatewaySLZ, MicroGatewaySLZ, UpdateMicroGatewaySLZ
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import Gateway, MicroGateway
from apigateway.tests.utils.testing import dummy_time

pytestmark = pytest.mark.django_db


class TestMicroGatewaySLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            # create_way: need_deploy
            (
                {
                    "create_way": "need_deploy",
                    "name": "color-green",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                {
                    "create_way": "need_deploy",
                    "name": "color-green",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "0.0.1",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
            ),
            # create_way: relate_deployed
            (
                {
                    "create_way": "relate_deployed",
                    "name": "color-green",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                {
                    "create_way": "relate_deployed",
                    "name": "color-green",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
            ),
            # invalid name
            (
                {
                    "create_way": "need_deploy",
                    "name": "invalid_name",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
                ValidationError,
            ),
            # bcs_info.project_id is required
            (
                {
                    "create_way": "need_deploy",
                    "name": "color-red",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, mocker, settings, data, expected, expected_error):
        settings.BCS_MICRO_GATEWAY_CHART_NAME = "bk-micro-gateway"
        settings.BCS_MICRO_GATEWAY_CHART_VERSION = "0.0.1"

        request = mocker.MagicMock(gateway=mocker.MagicMock())
        slz = MicroGatewaySLZ(data=data, context={"request": request})

        if expected_error:
            with pytest.raises(expected_error):
                slz.is_valid(raise_exception=True)
            return

        slz.is_valid(raise_exception=True)
        expected["gateway"] = request.gateway
        assert slz.validated_data == expected

    def test_to_representation(self, faker, settings):
        settings.BK_APIGATEWAY_API_URL = "http://bkapi-demo.example.com"

        gateway = G(Gateway)
        instance = G(
            MicroGateway,
            gateway=gateway,
            name=faker.color_name(),
            _config=json.dumps(
                {
                    "bcs": {
                        "project_id": faker.color_name(),
                        "project_name": faker.color_name(),
                        "cluster_id": faker.color_name(),
                        "namespace": faker.color_name(),
                        "chart_name": faker.color_name(),
                        "chart_version": "1.0.0",
                        "release_name": faker.color_name(),
                    },
                    "http": {"http_url": faker.url()},
                    "jwt_auth": {
                        "secret_key": faker.password(),
                    },
                }
            ),
            schema=SchemaFactory().get_micro_gateway_schema(),
        )

        slz = MicroGatewaySLZ(instance=instance)
        assert slz.data == {
            "id": str(instance.id),
            "name": instance.name,
            "description": instance.description,
            "bcs_info": instance.config["bcs"],
            "http_info": instance.config["http"],
            "jwt_auth_info": instance.config["jwt_auth"],
            "bk_apigateway_api_url": "http://bkapi-demo.example.com",
        }

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "create_way": "relate_deployed",
                    "name": "color-green",
                    "description": "test",
                    "bcs_info": {
                        "project_name": "demo",
                        "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": "bkapigw-demo",
                    },
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                {
                    "id": "519ff8e3-e22b-4043-893e-aaa1437187ce",
                    "name": "color-green",
                    "description": "test",
                    "is_shared": False,
                    "status": "installed",
                    "config": {
                        "bcs": {
                            "project_name": "demo",
                            "project_id": "bca1703a77f448e6bcd490ed8ffcfa6e",
                            "cluster_id": "demo-cluster",
                            "namespace": "demo-namespace",
                            "chart_name": "bk-micro-gateway",
                            "chart_version": "1.0.0",
                            "release_name": "bkapigw-demo",
                        },
                        "http": {
                            "http_url": "http://demo-bkapi.example.com",
                        },
                        "jwt_auth": {
                            "secret_key": "bca1703a77f448e6bcd490ed8ffcfa6e",
                        },
                    },
                },
            )
        ],
    )
    def test_create(self, mocker, data, expected):
        mocker.patch(
            "apigateway.apps.micro_gateway.serializers.uuid.uuid4", return_value="519ff8e3-e22b-4043-893e-aaa1437187ce"
        )
        mocker.patch(
            "apigateway.apps.micro_gateway.serializers.generate_unique_id",
            return_value="bca1703a77f448e6bcd490ed8ffcfa6e",
        )

        gateway = G(Gateway)
        request = mocker.MagicMock(gateway=gateway)
        slz = MicroGatewaySLZ(data=data, context={"request": request})
        slz.is_valid(raise_exception=True)

        instance = slz.save()

        config = instance.config
        expected_config = expected.pop("config")
        assert config == expected_config

        assert instance.status == expected.pop("status")

        for key, value in expected.items():
            assert getattr(instance, key) == value


class TestUpdateMicroGatewaySLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "name": "color-green",
                    "description": "test",
                    "is_shared": True,
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                {
                    "name": "color-green",
                    "description": "test",
                    "need_deploy": True,
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
            ),
            (
                {
                    "name": "color-green",
                    "description": "test",
                    "need_deploy": False,
                    "is_shared": True,
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                {
                    "name": "color-green",
                    "description": "test",
                    "need_deploy": False,
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
            ),
            # invalid name
            (
                {
                    "name": "invalid_name",
                    "description": "test",
                    "is_shared": True,
                    "http_info": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                },
                None,
                ValidationError,
            ),
            # invalid http_url
            (
                {
                    "name": "color-red",
                    "description": "test",
                    "is_shared": True,
                    "http_info": {
                        "http_url": "",
                    },
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, mocker, data, expected, expected_error):
        request = mocker.MagicMock(gateway=mocker.MagicMock())
        micro_gateway = G(MicroGateway)
        slz = UpdateMicroGatewaySLZ(micro_gateway, data=data, context={"request": request})

        if expected_error:
            with pytest.raises(expected_error):
                slz.is_valid(raise_exception=True)
            return

        slz.is_valid(raise_exception=True)
        expected["gateway"] = request.gateway
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data, current_config, expected",
        [
            (
                {
                    "name": "color-green",
                    "description": "test",
                    "http_info": {
                        "http_url": "http://new-demo-bkapi.example.com",
                    },
                },
                {
                    "bcs": {
                        "project_name": "demo",
                        "project_id": "eaccf209c7f14e8bb90874566be63c9f",
                        "cluster_id": "demo-cluster",
                        "namespace": "demo-namespace",
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": "bkapigw-demo",
                    },
                    "http": {
                        "http_url": "http://demo-bkapi.example.com",
                    },
                    "jwt_auth": {
                        "secret_key": "eaccf209c7f14e8bb90874566be63c9f",
                    },
                },
                {
                    "config": {
                        "bcs": {
                            "project_name": "demo",
                            "project_id": "eaccf209c7f14e8bb90874566be63c9f",
                            "cluster_id": "demo-cluster",
                            "namespace": "demo-namespace",
                            "chart_name": "bk-micro-gateway",
                            "chart_version": "1.0.0",
                            "release_name": "bkapigw-demo",
                        },
                        "http": {
                            "http_url": "http://new-demo-bkapi.example.com",
                        },
                        "jwt_auth": {
                            "secret_key": "eaccf209c7f14e8bb90874566be63c9f",
                        },
                    }
                },
            )
        ],
    )
    def test_update(self, mocker, data, current_config, expected):
        gateway = G(Gateway)
        micro_gateway = G(
            MicroGateway,
            _config=json.dumps(current_config),
            schema=SchemaFactory().get_micro_gateway_schema(),
        )

        request = mocker.MagicMock(gateway=gateway)
        slz = UpdateMicroGatewaySLZ(instance=micro_gateway, data=data, context={"request": request})
        slz.is_valid(raise_exception=True)

        instance = slz.save()
        assert instance.config == expected["config"]


class TestListMicroGatewaySLZ:
    def test_to_representation(self, faker, unique_id):
        gateway = G(Gateway)
        instance = G(
            MicroGateway,
            id=unique_id,
            gateway=gateway,
            name=faker.color_name(),
            _config=json.dumps(
                {
                    "bcs": {
                        "project_id": faker.color_name(),
                        "project_name": faker.color_name(),
                        "cluster_id": faker.color_name(),
                        "namespace": faker.color_name(),
                        "chart_name": "bk-micro-gateway",
                        "chart_version": "1.0.0",
                        "release_name": faker.color_name(),
                    },
                    "http": {"http_url": faker.url()},
                    "jwt_auth": {
                        "secret_key": faker.password(),
                    },
                }
            ),
            schema=SchemaFactory().get_micro_gateway_schema(),
        )
        instance.updated_time = dummy_time.time

        slz = ListMicroGatewaySLZ(
            [instance],
            many=True,
            context={
                "micro_gateway_id_to_stage_fields": {
                    instance.id: {
                        "id": unique_id,
                        "name": "prod",
                    }
                }
            },
        )
        assert slz.data == [
            {
                "id": instance.id,
                "name": instance.name,
                "description": instance.description,
                "status": instance.status,
                "comment": instance.comment,
                "updated_time": dummy_time.str,
                "chart_version": instance.config["bcs"]["chart_version"],
                "release_name": instance.config["bcs"]["release_name"],
                "stage_name": "prod",
            }
        ]

        slz = ListMicroGatewaySLZ([instance], many=True, context={"micro_gateway_id_to_stage_fields": {}})
        assert slz.data == [
            {
                "id": instance.id,
                "name": instance.name,
                "description": instance.description,
                "status": instance.status,
                "comment": instance.comment,
                "updated_time": dummy_time.str,
                "chart_version": instance.config["bcs"]["chart_version"],
                "release_name": instance.config["bcs"]["release_name"],
                "stage_name": "",
            }
        ]
