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
import contextlib
import logging
import time
from typing import Dict

import redis
from django.conf import settings
from redis.cluster import ClusterNode, RedisCluster
from redis.sentinel import Sentinel

from .exception import LockTimeout

logger = logging.getLogger(__name__)

REDIS_TIMEOUT = 2
REDIS_CLIENTS: Dict[str, redis.Redis] = {}

LOCK_KEY_PREFIX = "lock_"


def get_redis_pool(redis_conf):
    """
    @param redis_conf: redis 配置
    @return: redis 连接池
    """
    # support tls
    if redis_conf.get("tls_enabled"):
        return redis.BlockingConnectionPool(
            host=redis_conf["host"],
            port=redis_conf["port"],
            db=redis_conf.get("db", 0),
            password=redis_conf["password"],
            max_connections=redis_conf["max_connections"],
            socket_timeout=REDIS_TIMEOUT,
            timeout=REDIS_TIMEOUT,
            connection_class=redis.SSLConnection,
            ssl_ca_certs=redis_conf.get("tls_cert_ca_file"),
            ssl_certfile=redis_conf.get("tls_cert_file"),
            ssl_keyfile=redis_conf.get("tls_cert_key_file"),
            ssl_check_hostname=redis_conf.get("tls_check_hostname", False),
            # redis-py will send SETINFO command, not valid for older version redis
            lib_name=None,
            lib_version=None,
        )

    return redis.BlockingConnectionPool(
        host=redis_conf["host"],
        port=redis_conf["port"],
        db=redis_conf.get("db", 0),
        password=redis_conf["password"],
        max_connections=redis_conf["max_connections"],
        socket_timeout=REDIS_TIMEOUT,
        timeout=REDIS_TIMEOUT,
        # redis-py will send SETINFO command, not valid for older version redis
        lib_name=None,
        lib_version=None,
    )


def new_redis_client(redis_conf):
    """
    @param redis_conf: redis 配置，mode 支持 single / sentinel / cluster
    @return: redis client
    """
    mode = redis_conf.get("mode", "single")
    if mode == "single":
        # client 持有连接池，close 时一并断开连接
        return redis.Redis.from_pool(get_redis_pool(redis_conf))

    kwargs = {
        "password": redis_conf["password"],
        "max_connections": redis_conf["max_connections"],
        "socket_timeout": REDIS_TIMEOUT,
        "socket_connect_timeout": REDIS_TIMEOUT,
        # redis-py will send SETINFO command, not valid for older version redis
        "lib_name": None,
        "lib_version": None,
    }
    # support tls
    tls_kwargs = {
        "ssl": True,
        "ssl_ca_certs": redis_conf.get("tls_cert_ca_file") or None,
        "ssl_certfile": redis_conf.get("tls_cert_file") or None,
        "ssl_keyfile": redis_conf.get("tls_cert_key_file") or None,
        "ssl_check_hostname": redis_conf.get("tls_check_hostname", False),
    }
    redis_kwargs = {**kwargs, **tls_kwargs} if redis_conf.get("tls_enabled") else kwargs

    addrs = [addr.rsplit(":", 1) for addr in redis_conf["addrs"]]
    if mode == "sentinel":
        sentinel = Sentinel(
            [(host, int(port)) for host, port in addrs],
            # sentinel 节点的密码和 tls 与 redis 节点分开配置
            sentinel_kwargs={
                **kwargs,
                "password": redis_conf.get("sentinel_password"),
                **(tls_kwargs if redis_conf.get("sentinel_tls_enabled") else {}),
            },
            db=redis_conf.get("db", 0),
            **redis_kwargs,
        )
        return sentinel.master_for(redis_conf["sentinel_master_name"])

    if mode == "cluster":
        # redis cluster only support db 0
        return RedisCluster(startup_nodes=[ClusterNode(host, int(port)) for host, port in addrs], **redis_kwargs)

    raise ValueError(f"unsupported redis mode: {mode}")


def get_redis_client(name: str, redis_conf):
    if not redis_conf:
        return None

    redis_client = REDIS_CLIENTS.get(name)
    if redis_client and redis_client.ping():
        return redis_client

    try:
        redis_client = new_redis_client(redis_conf)
        redis_client.ping()
        REDIS_CLIENTS[name] = redis_client
        return redis_client
    except Exception:  # pylint: disable=broad-except
        logger.exception("connect to redis fail")
        return None


def get_default_redis_client():
    """Returns a default redis client"""
    return get_redis_client("default", getattr(settings, "DEFAULT_REDIS_CONFIG", None))


def get_redis_lock_name(name: str) -> str:
    """python-redis-lock 的 lua 脚本会同时操作 lock:{name} 和 lock-signal:{name}，
    redis cluster 下需要使用 hash tag 保证两个 key 在同一个 slot
    """
    if settings.DEFAULT_REDIS_CONFIG.get("mode") == "cluster":
        return f"{{{name}}}"
    return name


class Lock(object):
    def __init__(self, key, timeout=5, try_get_times=5):
        """初始化锁对象

        Args:
            key: 锁的 key
            timeout: 锁的过期时间，单位为秒，默认为 20 秒
            try_get_times: 尝试获取锁的次数，默认为 10 次
        """
        self.key = LOCK_KEY_PREFIX + key
        self.timeout = timeout
        self.try_get_times = try_get_times
        self.client = get_default_redis_client()

    def __enter__(self):
        """获取锁

        Returns:
            如果获取锁成功，返回 None；否则抛出 LockTimeout 异常
        """
        try_get_times = self.try_get_times
        while try_get_times > 0:
            # 尝试获取锁
            if self.client.lock(self.key, self.timeout).acquire(blocking=False):
                return
            # 获取锁失败，等待一段时间后重试
            try_get_times -= 1
            if try_get_times > 0:
                time.sleep(1)
        # 获取锁超时，抛出 LockTimeout 异常
        errmsg = "lock[key:%s] timeout|timeout:%s,try_get_times:%s" % (self.key, self.timeout, self.try_get_times)
        logger.error(errmsg)
        raise LockTimeout("Timeout while waiting for lock")

    def __exit__(self, exc_type, exc_value, traceback):
        """释放锁"""
        with contextlib.suppress(Exception):
            self.client.delete(self.key)
