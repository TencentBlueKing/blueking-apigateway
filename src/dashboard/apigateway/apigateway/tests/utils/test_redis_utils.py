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

from apigateway.utils.redis_utils import get_redis_lock_name, get_redis_pool, new_redis_client

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


@pytest.fixture
def redis_conf():
    return {
        "host": "localhost",
        "port": 6379,
        "addrs": ["node1:26379", "node2:26379"],
        "password": "test-password",
        "max_connections": 1,
        "db": 1,
        "sentinel_master_name": "mymaster",
        "sentinel_password": "sentinel-password",
    }


def test_new_redis_client_single(redis_conf):
    client = new_redis_client(redis_conf)

    assert isinstance(client.connection_pool, redis.BlockingConnectionPool)
    assert client.connection_pool.connection_kwargs["host"] == "localhost"


def test_new_redis_client_sentinel(mocker, redis_conf):
    sentinel = mocker.patch("apigateway.utils.redis_utils.Sentinel")
    redis_conf.update(mode="sentinel", tls_enabled=True, sentinel_tls_enabled=False)

    client = new_redis_client(redis_conf)

    assert client == sentinel.return_value.master_for.return_value
    sentinel.return_value.master_for.assert_called_once_with("mymaster")
    args, kwargs = sentinel.call_args
    assert args == ([("node1", 26379), ("node2", 26379)],)
    assert kwargs["db"] == 1
    assert kwargs["password"] == "test-password"
    assert kwargs["lib_name"] is None
    assert kwargs["ssl"] is True
    # sentinel 节点的密码和 tls 单独配置
    assert kwargs["sentinel_kwargs"]["password"] == "sentinel-password"
    assert "ssl" not in kwargs["sentinel_kwargs"]


def test_new_redis_client_cluster_with_tls(mocker, redis_conf):
    cluster = mocker.patch("apigateway.utils.redis_utils.RedisCluster")
    redis_conf.update(mode="cluster", tls_enabled=True, tls_cert_ca_file="/ca.pem")

    client = new_redis_client(redis_conf)

    assert client == cluster.return_value
    kwargs = cluster.call_args.kwargs
    assert [(node.host, node.port) for node in kwargs["startup_nodes"]] == [("node1", 26379), ("node2", 26379)]
    assert "db" not in kwargs
    assert kwargs["ssl"] is True
    assert kwargs["ssl_ca_certs"] == "/ca.pem"


@pytest.mark.parametrize("mode, expected", [("single", "test_lock"), ("cluster", "{test_lock}")])
def test_get_redis_lock_name(settings, mode, expected):
    settings.DEFAULT_REDIS_CONFIG = {"mode": mode}

    assert get_redis_lock_name("test_lock") == expected
