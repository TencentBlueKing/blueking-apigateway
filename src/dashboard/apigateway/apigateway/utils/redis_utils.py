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
import logging
from typing import Dict

import redis
from django.conf import settings
from redis import sentinel

logger = logging.getLogger(__name__)

REDIS_TIMEOUT = 2
REDIS_CLIENTS: Dict[str, redis.Redis] = {}


def get_redis_pool(redis_conf):
    """
    @param redis_conf: redis 配置
    @return: redis 连接池
    """

    if redis_conf.get("use_sentinel", False):
        redis_sentinel = sentinel.Sentinel(
            redis_conf["sentinels"],
            sentinel_kwargs={"password": redis_conf["sentinel_password"], "socket_timeout": REDIS_TIMEOUT},
            socket_timeout=REDIS_TIMEOUT,
        )
        return sentinel.SentinelConnectionPool(
            redis_conf["master_name"],
            redis_sentinel,
            db=redis_conf.get("db", 0),
            password=redis_conf["password"],
            max_connections=redis_conf["max_connections"],
        )
    else:
        return redis.BlockingConnectionPool(
            host=redis_conf["host"],
            port=redis_conf["port"],
            db=redis_conf.get("db", 0),
            password=redis_conf["password"],
            max_connections=redis_conf["max_connections"],
            socket_timeout=REDIS_TIMEOUT,
            timeout=REDIS_TIMEOUT,
        )


def get_redis_client(name: str, redis_conf):
    if not redis_conf:
        return None

    redis_client = REDIS_CLIENTS.get(name)
    if redis_client and redis_client.ping():
        return redis_client

    try:
        redis_client = redis.Redis(connection_pool=get_redis_pool(redis_conf))
        redis_client.ping()
        REDIS_CLIENTS[name] = redis_client
        return redis_client
    except Exception:
        logger.exception("connect to redis fail")
        return None


def get_default_redis_client():
    """Returns a default redis client"""
    return get_redis_client("default", getattr(settings, "DEFAULT_REDIS_CONFIG", None))


def get_redis_key(key):
    """Get redis key with prefix"""
    return f"{settings.REDIS_PREFIX}{key}"
