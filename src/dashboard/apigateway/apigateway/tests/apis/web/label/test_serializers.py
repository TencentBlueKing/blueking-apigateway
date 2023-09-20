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

from apigateway.apis.web.label.serializers import GatewayLabelInputSLZ, GatewayLabelOutputSLZ
from apigateway.apps.label.models import APILabel


class TestGatewayLabelOutputSLZ:
    def test_to_representation(self):
        label = G(APILabel)

        expected = {
            "id": label.id,
            "name": label.name,
        }

        slz = GatewayLabelOutputSLZ(instance=label)
        assert slz.data == expected


class TestGatewayLabelInputSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            # ok
            (
                {
                    "id": 1,
                    "name": "foo",
                },
                {
                    "name": "foo",
                },
            ),
            # fail, name exists
            (
                {
                    "name": "exist",
                },
                None,
            ),
        ],
    )
    def test_validate(self, fake_gateway, data, expected):
        G(APILabel, gateway=fake_gateway, name="exist")

        slz = GatewayLabelInputSLZ(data=data, context={"gateway": fake_gateway})
        slz.is_valid()

        if expected is None:
            assert slz.errors
            return

        expected["gateway"] = fake_gateway
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data, expected",
        [
            # ok
            (
                {
                    "name": "foo",
                },
                {
                    "name": "foo",
                },
            ),
            # ok, update with old-name
            (
                {
                    "name": "exist",
                },
                {
                    "name": "exist",
                },
            ),
            # error, update with other-exist
            (
                {
                    "name": "other-exist",
                },
                None,
            ),
        ],
    )
    def test_validate_update(self, fake_gateway, data, expected):
        instance = G(APILabel, gateway=fake_gateway, name="exist")
        G(APILabel, gateway=fake_gateway, name="other-exist")

        slz = GatewayLabelInputSLZ(instance=instance, data=data, context={"gateway": fake_gateway})
        slz.is_valid()

        if expected is None:
            assert slz.errors
            return

        expected["gateway"] = fake_gateway
        assert slz.validated_data == expected
