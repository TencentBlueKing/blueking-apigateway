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

import time

import pytest

from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock


# 定义一个 mock Redis 客户端对象
class MockRedisClient:
    def __init__(self):
        self.data = {}

    def setnx(self, key, value):
        if key in self.data:
            return False
        self.data[key] = value
        return True

    def expire(self, key, timeout):
        pass

    def delete(self, key):
        if key in self.data:
            del self.data[key]

    def get(self, key):
        return self.data.get(key)


# 定义 Redis 客户端的 fixture
@pytest.fixture(scope="function")
def redis_client():
    client = MockRedisClient()
    yield client
    client.data = {}


# 测试 Lock 对象的基本功能
def test_lock_basic(redis_client):
    # 创建一个锁对象
    lock = Lock("test_lock")
    lock.client = redis_client

    # 获取锁
    with lock:
        # 模拟持有锁时的操作
        time.sleep(1)

    # 确认锁已经被释放
    assert redis_client.get("lock_test_lock") is None


# 测试 Lock 对象的超时功能
def test_lock_timeout(redis_client):
    # 创建一个锁对象
    lock = Lock("test_lock", timeout=2, try_get_times=2)
    lock.client = redis_client

    # 获取锁
    with lock:
        # 模拟持有锁时的操作
        time.sleep(3)

    # 确认锁已经被释放
    assert redis_client.get("lock_test_lock") is None


def test_lock_acquire_failed(redis_client):
    # 创建一个锁对象
    lock1 = Lock("test_lock", timeout=2, try_get_times=1)
    lock1.client = redis_client

    lock2 = Lock("test_lock", timeout=2, try_get_times=1)
    lock2.client = redis_client

    # 获取锁1
    with lock1:
        # 模拟持有锁时的操作
        time.sleep(1)

        # 获取锁2，期望获取锁失败
        with pytest.raises(LockTimeout):
            with lock2:
                # 模拟持有锁时的操作
                time.sleep(1)

    # 获取锁2，期望获取锁成功
    with lock2:
        # 模拟持有锁时的操作
        time.sleep(1)

    # 确认锁已经被释放
    assert redis_client.get("lock_test_lock") is None
