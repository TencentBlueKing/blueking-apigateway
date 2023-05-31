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


@pytest.fixture
def fake_node_data(faker, unique_backend_service_name):
    return {
        "name": unique_backend_service_name,
        "description": faker.pystr(),
        "loadbalance": "roundrobin",
        "upstream_type": "node",
        "stage_item_id": None,
        "upstream_custom_config": {
            "nodes": [
                {
                    "host": "1.0.0.1:8000",
                    "weight": 100,
                }
            ]
        },
        "pass_host": "pass",
        "scheme": "http",
        "timeout": {"connect": 10, "send": 10, "read": 10},
        "ssl_enabled": False,
    }


@pytest.fixture
def fake_service_discovery_data(faker, unique_backend_service_name):
    return {
        "name": unique_backend_service_name,
        "description": faker.pystr(),
        "loadbalance": "roundrobin",
        "upstream_type": "service_discovery",
        "stage_item_id": None,
        "upstream_custom_config": {
            "discovery_type": "go_micro_etcd",
            "discovery_config": {
                "addresses": ["1.0.0.1:8000"],
                "secure_type": "ssl",
                "ssl_certificate_id": 10,
            },
        },
        "upstream_config": {
            "service_name": "my-service",
        },
        "pass_host": "rewrite",
        "upstream_host": "test.blueking.com",
        "scheme": "http",
        "timeout": {"connect": 10, "send": 10, "read": 10},
        "ssl_enabled": True,
    }
