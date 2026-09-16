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
from threading import RLock

from cachetools import TTLCache
from django.conf import settings

from apigateway.common.constants import CACHE_MAXSIZE
from apigateway.components.bkiam import direct_auth

from .constants import ALLOW_CACHE_TTL

_allow_cache: TTLCache[tuple[str, int, str], bool] = TTLCache(maxsize=CACHE_MAXSIZE, ttl=ALLOW_CACHE_TTL)
_allow_cache_lock = RLock()


def is_iam_auth_active() -> bool:
    return settings.BK_IAM_V4_ENABLED


def clear_gateway_iam_auth_cache() -> None:
    with _allow_cache_lock:
        _allow_cache.clear()


def is_iam_gateway_action_allowed(username: str, gateway_id: int, action: str) -> bool:
    cache_key = (username, gateway_id, action)
    with _allow_cache_lock:
        if cache_key in _allow_cache:
            return True

    allowed = direct_auth(
        {
            "subject": {"type": "user", "id": username},
            "action_id": action,
            "resource": {"id": str(gateway_id)},
        }
    )
    if allowed:
        with _allow_cache_lock:
            _allow_cache[cache_key] = True
    return allowed
