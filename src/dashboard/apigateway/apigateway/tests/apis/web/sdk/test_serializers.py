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

from apigateway.apis.web.sdk.serializers import GatewaySDKListOutputSLZ
from apigateway.apps.support.api_sdk.models import SDKFactory
from apigateway.apps.support.models import GatewaySDK
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import ResourceVersion
from apigateway.tests.utils.testing import dummy_time


class TestSDKListOutputSLZ:
    def test_to_representation(self, fake_gateway):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1", title="test")
        sdk_1 = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            name="bkapigw-test",
            version_number="12345",
            _config=json.dumps({"python": {"is_uploaded_to_pypi": True}}),
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
            created_by="test",
            url="http://bking.com/pypi/bkapigw-test/12345/bkapigw-test-12345.tar.gz",
        )
        sdks = [SDKFactory.create(model=sdk_1)]
        slz = GatewaySDKListOutputSLZ(
            instance=sdks,
            many=True,
        )
        print(slz.data)
        assert slz.data == [
            {
                "id": sdk_1.id,
                "language": "python",
                "name": "bkapigw-test",
                "version_number": "12345",
                "created_time": dummy_time.str,
                "created_by": "test",
                "updated_time": dummy_time.str,
                "download_url": "http://bking.com/pypi/bkapigw-test/12345/bkapigw-test-12345.tar.gz",
                "resource_version": {
                    "id": resource_version.id,
                    "version": resource_version.version,
                },
            },
        ]
