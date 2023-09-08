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

from django_dynamic_fixture import G

from apigateway.apps.support.api_sdk.models import SDKContext
from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.apps.support.models import APISDK
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import ResourceVersion
from apigateway.tests.utils.testing import dummy_time


class TestAPISDKListCreateApi:
    def test_list(self, request_view, fake_gateway, settings):

        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1", title="test")
        sdk_1 = G(
            APISDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            name="bkapigw-test",
            version_number="12345",
            _config=json.dumps({"python": {"is_uploaded_to_pypi": True}}),
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
            url="http://bking.com/pypi/bkapigw-test/12345/bkapigw-test-12345.tar.gz",
        )

        sdk_2 = G(
            APISDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            name="bkapigw-test",
            version_number="1234512",
            _config=json.dumps({"python": {"is_uploaded_to_pypi": False}}),
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
        )

        data = [
            {
                "gateway": fake_gateway,
                "params": {
                    "language": "python",
                    "resource_version_id": resource_version.id,
                },
                "expected": {
                    "count": 2,
                    "has_next": False,
                    "has_previous": False,
                    "results": [
                        {
                            "config": {"is_uploaded_to_pypi": False},
                            "id": sdk_2.id,
                            "language": "python",
                            "name": "bkapigw-test",
                            "version_number": "1234512",
                            "created_time": dummy_time.str,
                            "updated_time": dummy_time.str,
                            "created_by": None,
                            "download_url": "",
                            "is_uploaded_to_pypi": False,
                            "resource_version_id": resource_version.id,
                            "resource_version_name": resource_version.name,
                            "resource_version_title": resource_version.title,
                            "resource_version_display": "1.0.1(test)",
                        },
                        {
                            "config": {"is_uploaded_to_pypi": True},
                            "id": sdk_1.id,
                            "language": "python",
                            "name": "bkapigw-test",
                            "version_number": "12345",
                            "created_time": dummy_time.str,
                            "created_by": None,
                            "updated_time": dummy_time.str,
                            "download_url": "http://bking.com/pypi/bkapigw-test/12345/bkapigw-test-12345.tar.gz",
                            "is_uploaded_to_pypi": True,
                            "resource_version_id": resource_version.id,
                            "resource_version_name": resource_version.name,
                            "resource_version_title": resource_version.title,
                            "resource_version_display": "1.0.1(test)",
                        },
                    ],
                },
            },
        ]

        for test in data:
            resp = request_view(
                method="GET",
                view_name="support.api_sdk.list_create",
                gateway=fake_gateway,
                path_params={"gateway_id": fake_gateway.id},
                data=test["params"],
            )

            result = resp.json()

            assert result["data"] == test["expected"]

    def test_create(self, request_view, fake_gateway, mocker):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1", title="test")

        mocker.patch(
            "apigateway.apps.support.api_sdk.managers.python.SDKManager.handle",
            return_value=SDKContext(
                name=f"bkapigw-{fake_gateway.name}",
                resource_version=resource_version,
                language=ProgrammingLanguageEnum.PYTHON,
                version="2",
                config={"python": {"is_uploaded_to_pypi": True}},
                is_latest=True,
                is_distributed=True,
                files=[f"bkapigw-{fake_gateway.name}-2.tar.gz"],
            ),
        )

        data = [
            {
                "gateway": fake_gateway,
                "params": {
                    "resource_version_id": resource_version.id,
                    "language": "python",
                    "include_private_resources": False,
                    "need_upload_to_pypi": True,
                },
                "expected": {
                    "name": f"bkapigw-{fake_gateway.name}",
                    "is_uploaded_to_pypi": True,
                    "language": "python",
                    "version_number": "2",
                    "resource_version_id": resource_version.id,
                    "resource_version_name": resource_version.name,
                    "resource_version_title": resource_version.title,
                    "resource_version_display": "1.0.1(test)",
                },
            },
        ]
        for test in data:
            resp = request_view(
                method="POST",
                view_name="support.api_sdk.list_create",
                gateway=fake_gateway,
                path_params={"gateway_id": fake_gateway.id},
                data=test["params"],
            )

            result = resp.json()
            assert result["data"]["name"] == test["expected"]["name"]
            assert result["data"]["is_uploaded_to_pypi"] == test["expected"]["is_uploaded_to_pypi"]
            assert result["data"]["language"] == test["expected"]["language"]
            assert result["data"]["resource_version_id"] == test["expected"]["resource_version_id"]
            assert result["data"]["resource_version_name"] == test["expected"]["resource_version_name"]
