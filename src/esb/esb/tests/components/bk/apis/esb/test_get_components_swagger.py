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
import operator

import pytest
from ddf import G

from components.bk.apis.esb.get_components_swagger import GetComponentsSwagger
from esb.bkcore.constants import DataTypeEnum
from esb.bkcore.models import ESBChannel, System

pytestmark = pytest.mark.django_db


class TestGetComponentsSwagger:
    @pytest.fixture(autouse=True)
    def fake_component(self):
        self.fake_component = GetComponentsSwagger()

    @pytest.mark.parametrize(
        "data, expected",
        [
            ({"token": "fake-token"}, True),
            ({"token": ""}, False),
            ({"token": "invalid-token"}, False),
        ],
    )
    def test_form(self, settings, data, expected):
        settings.ESB_COMPONENTS_SWAGGER_TOKEN = "fake-token"

        form = GetComponentsSwagger.Form(data=data)
        assert form.is_valid() == expected

    def test_get_available_components(self, faker):
        board = faker.uuid4()
        system = G(System, board=board)

        G(
            ESBChannel,
            system=system,
            board=board,
            method=faker.http_method(),
            path=faker.unique.pystr(),
            is_public=True,
            is_active=True,
            data_type=DataTypeEnum.OFFICIAL_PUBLIC.value,
            config={"suggest_method": faker.http_method()},
        )
        # suggest_method and method is empty
        G(
            ESBChannel,
            board=board,
            method="",
            path=faker.unique.pystr(),
            is_public=True,
            is_active=True,
            data_type=DataTypeEnum.OFFICIAL_PUBLIC.value,
            system=system,
            config={},
        )
        G(
            ESBChannel,
            board=board,
            method=faker.http_method(),
            path=faker.unique.pystr(),
            is_public=True,
            is_active=True,
            data_type=DataTypeEnum.OFFICIAL_PUBLIC.value,
            system=system,
            config={"suggest_method": faker.http_method(), "no_sdk": True},
        )

        assert len(self.fake_component._get_available_components(board)) == 1

    def test_deduplicate_and_enrich_components(self):
        components = [
            {"path": "/v2/color/red/"},
            {"path": "/v2/color/green/"},
            {"path": "/color/red/"},
            {"path": "/color/orange/"},
        ]
        result = sorted(
            self.fake_component._deduplicate_and_enrich_components(components),
            key=operator.itemgetter("path"),
        )
        assert result == [
            {"path": "/api/c/compapi{bk_api_ver}/color/green/"},
            {"path": "/api/c/compapi{bk_api_ver}/color/orange/"},
            {"path": "/api/c/compapi{bk_api_ver}/color/red/"},
        ]

    def test_generate_swagger_paths(self):
        components = [
            {
                "method": "POST",
                "path": "/color/red",
                "name": "test",
                "description": "desc",
                "system_name": "DEMO",
            },
        ]
        result = self.fake_component._generate_swagger_paths(components)
        assert result == {
            "/color/red": {
                "post": {
                    "operationId": "demo_test",
                    "description": "desc",
                    "tags": ["demo"],
                    "x-component-name": "test",
                }
            }
        }
