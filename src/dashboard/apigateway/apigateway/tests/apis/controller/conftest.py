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

from ddf import G
from pytest import fixture

from apigateway.core.models import MicroGateway


@fixture
def micro_gateway_http_domain(faker):
    return faker.domain_name()


@fixture
def micro_gateway_http_port(faker):
    return faker.pyint(min_value=1, max_value=65535)


@fixture
def micro_gateway_http_path(faker):
    return f"/{faker.word()}"


@fixture
def micro_gateway_http_url(micro_gateway_http_domain, micro_gateway_http_port, micro_gateway_http_path):
    return f"http://{micro_gateway_http_domain}:{micro_gateway_http_port}{micro_gateway_http_path}"


@fixture
def micro_gateway(faker, micro_gateway_http_url, micro_gateway_schema, settings):
    gateway = G(
        MicroGateway,
        name=faker.color_name(),
        schema=micro_gateway_schema,
        is_shared=True,
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
                "metadata": {
                    "is_managed": True,
                },
                "http": {
                    "http_url": micro_gateway_http_url,
                },
                "jwt_auth": {
                    "secret_key": faker.password(),
                },
            }
        ),
    )

    settings.DEFAULT_MICRO_GATEWAY_ID = gateway.id
    return gateway
