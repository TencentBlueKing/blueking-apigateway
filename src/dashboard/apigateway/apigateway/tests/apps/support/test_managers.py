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

from apigateway.apps.support.models import (
    GatewaySDK,
    ReleasedResourceDoc,
)
from apigateway.core.models import ResourceVersion
from apigateway.tests.utils.testing import create_gateway

pytestmark = pytest.mark.django_db


class TestAPISDKManager:
    def test_filter_resource_version_ids_has_sdk(self):
        gateway = create_gateway()

        rv_1 = G(ResourceVersion, gateway=gateway)
        rv_2 = G(ResourceVersion, gateway=gateway)
        rv_3 = G(ResourceVersion, gateway=gateway)

        G(GatewaySDK, gateway=gateway, resource_version=rv_1)
        G(GatewaySDK, gateway=gateway, resource_version=rv_3)

        data = [
            {
                "params": {
                    "resource_version_ids": [rv_1.id, rv_2.id, rv_3],
                },
                "expected": [rv_1.id, rv_3.id],
            },
            {
                "params": {
                    "resource_version_ids": [rv_2.id],
                },
                "expected": [],
            },
        ]
        for test in data:
            result = GatewaySDK.objects.filter_resource_version_ids_has_sdk(
                gateway.id,
                test["params"]["resource_version_ids"],
            )
            assert result == test["expected"]

    def test_filter_resource_version_public_latest_sdk(self):
        gateway = create_gateway()

        rv_1 = G(ResourceVersion, gateway=gateway)
        rv_2 = G(ResourceVersion, gateway=gateway)
        rv_3 = G(ResourceVersion, gateway=gateway)

        G(
            GatewaySDK,
            gateway=gateway,
            resource_version=rv_1,
            language="python",
            is_public=True,
        )
        G(
            GatewaySDK,
            gateway=gateway,
            resource_version=rv_1,
            language="python",
            is_public=False,
        )
        sdk3 = G(
            GatewaySDK,
            gateway=gateway,
            resource_version=rv_1,
            language="python",
            is_public=True,
        )
        G(
            GatewaySDK,
            gateway=gateway,
            resource_version=rv_2,
            language="python",
            is_public=False,
        )
        sdk5 = G(
            GatewaySDK,
            gateway=gateway,
            resource_version=rv_3,
            language="python",
            is_public=True,
        )

        result = GatewaySDK.objects.filter_resource_version_public_latest_sdk(
            gateway.id,
            resource_version_ids=[rv_1.id, rv_2.id, rv_3.id],
        )
        assert result == {
            rv_1.id: sdk3,
            rv_3.id: sdk5,
        }


class TestReleasedResourceDocManager:
    def test_get_doc_updated_time(self, fake_resource_version, fake_resource1):
        fake_gateway = fake_resource_version.gateway
        G(
            ReleasedResourceDoc,
            gateway=fake_gateway,
            resource_version_id=fake_resource_version.id,
            resource_id=fake_resource1.id,
            language="zh",
            data={"updated_time": "1970-10-10 12:10:20"},
        )

        result = ReleasedResourceDoc.objects.get_doc_updated_time(
            fake_gateway.id,
            fake_resource_version.id,
            fake_resource1.id,
        )
        assert result == {"zh": "1970-10-10 12:10:20"}
