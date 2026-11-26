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

from apigateway.common import cache
from apigateway.common.cache import cache_on_arguments

pytestmark = pytest.mark.no_meta_schema


@pytest.fixture
def redis_client(mocker):
    client = mocker.MagicMock()
    mocker.patch("apigateway.common.cache.new_redis_client", return_value=client)
    cache.get_cache_redis_client.cache_clear()
    region = cache._make_region(60, cache.REDIS_EXPIRATION_GRACE_SECONDS)
    yield client, region
    cache.get_cache_redis_client.cache_clear()


def test_cache_on_arguments(mocker):
    source = mocker.Mock(side_effect=lambda a, b: a + b)

    class Foo:
        @cache_on_arguments(expiration_time=300)
        def add(self, a, b=1):
            return source(a, b)

    assert Foo().add(1) == 2
    assert Foo().add(1, b=1) == 2
    assert Foo().add(a=1, b=1) == 2
    assert source.call_count == 1

    # self is ignored in the key, but invalidate needs it to be passed
    Foo.add.invalidate(Foo(), 1)
    assert Foo().add(1) == 2
    assert source.call_count == 2


@pytest.mark.parametrize("args1, args2", [((None,), ("None",)), (("x None", None), ("x", "None None"))])
def test_cache_key_not_conflict(mocker, args1, args2):
    source = mocker.Mock(side_effect=lambda a, b=None: (a, b))

    @cache_on_arguments(expiration_time=300)
    def get_value(a, b=None):
        return source(a, b)

    assert get_value(*args1) != get_value(*args2)
    assert source.call_count == 2


def test_redis_key_and_expiration(mocker, settings, redis_client):
    client, region = redis_client
    client.get.return_value = None
    mocker.patch.dict(cache._SHARED_REGIONS, {60: region})

    @cache_on_arguments(expiration_time=60, namespace="v1")
    def get_value(a, b):
        return a

    assert get_value(1, "b") == 1
    key = f"{settings.REDIS_PREFIX}cache:{__name__}:get_value|v1|1 'b'"
    client.get.assert_called_with(key)
    assert client.setex.call_args.args[:2] == (key, 60 + cache.REDIS_EXPIRATION_GRACE_SECONDS)


def test_redis_error_fallback_to_source(redis_client):
    client, region = redis_client
    client.get.side_effect = redis.ConnectionError()
    client.setex.side_effect = redis.ConnectionError()

    @region.cache_on_arguments()
    def get_value(a):
        return a

    assert get_value(1) == 1
    client.setex.assert_called_once()


def test_redis_expiration_grace(redis_client):
    client, _ = redis_client
    client.get.return_value = None

    @cache._make_region(60, redis_expiration_grace=0).cache_on_arguments()
    def get_value(a):
        return a

    get_value(1)
    assert client.setex.call_args.args[1] == 60


def test_deserialize_error_fallback_to_source(redis_client):
    client, region = redis_client
    client.get.return_value = b'{"ct": 9999999999, "v": 2}|invalid pickle data'

    @region.cache_on_arguments()
    def get_value(a):
        return a

    assert get_value(1) == 1
    client.setex.assert_called_once()
