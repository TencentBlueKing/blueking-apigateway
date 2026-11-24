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
"""
共享缓存，基于 dogpile.cache，数据存储在 redis 中，支持 single / sentinel / cluster 模式

用法：
    from apigateway.common.cache import cache_on_arguments, get_region

    # 按函数参数缓存，kwargs 与 dogpile 的 CacheRegion.cache_on_arguments 一致，如 namespace、should_cache_fn
    @cache_on_arguments(expiration_time=300)
    def get_xxx(a, b=None): ...

    get_xxx.invalidate(a, b=None)  # 删除缓存；方法需传入 self，如 Foo.get_xxx.invalidate(foo, a)

    # 参数无法作为 key 时（如 ORM 对象、用户凭据），自行生成 key，使用 dogpile 的 region 接口
    _xxx_cache = get_region(300)  # 在模块级别获取
    _xxx_cache.get_or_create(f"xxx:{obj.id}", lambda: get_xxx(obj, user_credentials))

缓存 key：
- 由模块名、函数名、namespace 和参数（忽略 self / cls）生成，参数应为 int、str 等简单类型，不要传入 ORM 对象、request 等
- 同一模块中不同类的同名方法，需设置不同的 namespace

缓存值：
- 使用 pickle 序列化，建议只缓存内置类型；读取时会反序列化 redis 中的数据，redis 不要与不可信方共用
- 处理逻辑或返回值结构调整时，需更新 namespace，使旧缓存失效

删除：
- 删除指定缓存：使用被装饰函数的 invalidate，或 region.delete
- 不要调用 get_region 返回的 region 的 invalidate()：该 region 由相同缓存时长的缓存共用，且 invalidate() 只在当前进程生效；
  确需整体清除时，使用 new_region 创建独立的 region

异常：redis 异常、缓存值无法反序列化（pickle）时，按未命中处理
"""

import functools
import logging
import pickle
from typing import TYPE_CHECKING

from django.conf import settings
from dogpile.cache import make_region, register_backend
from dogpile.cache.api import NO_VALUE, CantDeserializeException
from dogpile.cache.backends import redis as redis_backend
from dogpile.cache.util import kwarg_function_key_generator

from apigateway.utils.redis_utils import new_redis_client

if TYPE_CHECKING:
    from dogpile.cache.region import CacheRegion

logger = logging.getLogger(__name__)

# redis 中 key 比缓存时长多保留一段时间：缓存过期后，同一进程内由一个线程回源，其他线程先返回旧值
REDIS_EXPIRATION_GRACE_SECONDS = 60


@functools.cache
def get_cache_redis_client():
    """所有 region 共用一个 client；cluster 模式创建 client 时会连接 redis，因此在首次使用时创建"""
    return new_redis_client(settings.DEFAULT_REDIS_CONFIG)


def _deserialize(value: bytes):
    # 数据损坏、缓存的类被修改等导致无法反序列化时，按未命中处理
    try:
        return pickle.loads(value)
    except Exception as err:  # pylint: disable=broad-except
        logger.exception("deserialize cache fail")
        raise CantDeserializeException from err


class RedisBackend(redis_backend.RedisBackend):
    """使用 DEFAULT_REDIS_CONFIG 连接 redis，读写异常时按未命中处理"""

    deserializer = staticmethod(_deserialize)

    def _create_client(self):
        pass

    @property
    def writer_client(self):
        return get_cache_redis_client()

    @property
    def reader_client(self):
        return get_cache_redis_client()

    def get_serialized(self, key):
        try:
            return super().get_serialized(key)
        except Exception:  # pylint: disable=broad-except
            logger.exception("get cache from redis fail, key=%s", key)
            return NO_VALUE

    def set_serialized(self, key, value):
        try:
            super().set_serialized(key, value)
        except Exception:  # pylint: disable=broad-except
            logger.exception("set cache to redis fail, key=%s", key)


register_backend("apigateway.redis", __name__, "RedisBackend")


def _mangle_key(key: str) -> str:
    return f"{settings.REDIS_PREFIX}cache:{key}"


def _make_region(expiration_time: int, redis_expiration_grace: int) -> CacheRegion:
    return make_region(
        # 支持关键字参数和默认参数，并忽略方法的 self / cls
        function_key_generator=kwarg_function_key_generator,
        key_mangler=_mangle_key,
    ).configure(
        "apigateway.redis",
        expiration_time=expiration_time,
        arguments={"redis_expiration_time": expiration_time + redis_expiration_grace},
    )


# 所有 region，测试中替换为内存 backend
CACHE_REGIONS: list[CacheRegion] = []
# redis 中 key 的过期时间只能在 region 上配置，因此按缓存时长共用 region
_SHARED_REGIONS: dict[int, CacheRegion] = {}


def new_region(expiration_time: int, redis_expiration_grace: int = REDIS_EXPIRATION_GRACE_SECONDS) -> CacheRegion:
    """创建独立的 region，用于需要通过 region.invalidate() 整体清除，或不能返回过期值（redis_expiration_grace=0）的缓存"""
    region = _make_region(expiration_time, redis_expiration_grace)
    CACHE_REGIONS.append(region)
    return region


def get_region(expiration_time: int) -> CacheRegion:
    """获取缓存时长为 expiration_time 秒的 region，相同时长的缓存共用"""
    if expiration_time not in _SHARED_REGIONS:
        _SHARED_REGIONS[expiration_time] = new_region(expiration_time)
    return _SHARED_REGIONS[expiration_time]


def cache_on_arguments(expiration_time: int, **kwargs):
    """按函数参数缓存返回值，kwargs 与 dogpile 的 CacheRegion.cache_on_arguments 一致"""
    # dogpile 默认用 str 转换参数后以空格拼接，None 与 "None"、("a b", None) 与 ("a", "b None") 的 key 相同；
    # 使用 repr 转换，字符串带引号，不会冲突
    kwargs.setdefault("to_str", repr)
    return get_region(expiration_time).cache_on_arguments(**kwargs)
