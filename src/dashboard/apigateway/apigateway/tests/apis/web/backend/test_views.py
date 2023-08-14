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

from apigateway.tests.utils.testing import dummy_time

pytestmark = pytest.mark.django_db


class TestBackendCreateApi:
    def test_create(self, mocker, request_view, fake_stage):
        mocker.patch("apigateway.biz.backend.BackendHandler.create", return_value=dummy_time.time)
        fake_gateway = fake_stage.api

        data = [
            {
                "name": "backend-test",
                "description": "test",
                "type": "http",
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "type": "node",
                        "timeout": 1,
                        "loadbalance": "roundrobin",
                        "hosts": [{"schema": "http", "host": "www.example.com", "weight": 1}],
                    }
                ],
            }
        ]

        for test in data:
            response = request_view(
                "POST",
                "backend.list-create",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data=test,
            )
            assert response.status_code == 201
