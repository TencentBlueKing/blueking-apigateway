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
import pytest
import redis

from apigateway.utils.redis_utils import get_redis_pool

pytestmark = pytest.mark.no_meta_schema


@pytest.mark.parametrize("tls_enabled", [False, True])
@pytest.mark.parametrize("password", ["", "test-password"])
def test_connect_to_redis_without_hello_support(mocker, tls_enabled, password):
    pool = get_redis_pool(
        {
            "host": "localhost",
            "port": 6379,
            "password": password,
            "max_connections": 1,
            "tls_enabled": tls_enabled,
        }
    )
    connection = pool.make_connection()

    def send_command(command, *args, **kwargs):
        if command == "HELLO":
            raise redis.ResponseError("unknown command 'HELLO'")

    # Exercise redis-py's real handshake with only the socket I/O replaced.
    mocker.patch.object(connection, "_connect", return_value=mocker.Mock())
    mocker.patch.object(connection, "send_command", side_effect=send_command)
    mocker.patch.object(connection, "read_response", return_value=b"OK")
    try:
        connection.connect()
    finally:
        connection.disconnect()
