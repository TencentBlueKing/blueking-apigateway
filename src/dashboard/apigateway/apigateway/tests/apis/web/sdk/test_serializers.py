# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from django_dynamic_fixture import G

from apigateway.apis.web.sdk.serializers import GatewaySDKGenerateInputSLZ, GatewaySDKListOutputSLZ
from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.sdk import SDKFactory
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import ResourceVersion
from apigateway.tests.utils.testing import dummy_time


class TestGatewaySDKGenerateInputSLZ:
    @pytest.mark.parametrize(
        "languages, is_valid",
        [
            (["python"], True),
            (["python", "java", "go", "javascript", "rust"], True),
            ([], False),
            (["unknown"], False),
        ],
    )
    def test_validate_languages(self, fake_gateway, languages, is_valid):
        slz = GatewaySDKGenerateInputSLZ(
            data={
                "resource_version_id": 1,
                "languages": languages,
            },
            context={"gateway": fake_gateway},
        )

        assert slz.is_valid() is is_valid
        if not is_valid:
            assert "languages" in slz.errors

    def test_languages_are_required(self, fake_gateway):
        slz = GatewaySDKGenerateInputSLZ(data={"resource_version_id": 1}, context={"gateway": fake_gateway})

        assert not slz.is_valid()
        assert "languages" in slz.errors


class TestSDKListOutputSLZ:
    def test_to_representation(self, fake_gateway):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
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
