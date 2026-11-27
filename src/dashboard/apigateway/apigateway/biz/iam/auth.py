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
from typing import TYPE_CHECKING

from django.conf import settings

from apigateway.common.cache import new_region

from .authorization import check_gateway_authorization
from .constants import ALLOW_CACHE_TTL

if TYPE_CHECKING:
    from apigateway.core.models import Gateway

# 只缓存允许的结果，避免授权后仍被拒绝；使用独立的 region，以便整体清除；
# redis 中不多保留过期的结果，避免权限回收后，回源期间仍返回过期的允许结果
_allow_cache = new_region(ALLOW_CACHE_TTL, redis_expiration_grace=0)


def is_iam_auth_active() -> bool:
    return settings.BK_IAM_V4_ENABLED


def clear_gateway_iam_auth_cache() -> None:
    # 与进程内缓存时一样，只清除当前进程的缓存
    _allow_cache.invalidate()


def is_iam_gateway_action_allowed(gateway: Gateway, username: str, action: str) -> bool:
    return _allow_cache.get_or_create(
        f"iam_gateway_action_allowed:{gateway.id}:{username}:{action}",
        lambda: check_gateway_authorization(
            gateway,
            {
                "subject": {"type": "user", "id": username},
                "action_id": action,
                "resource": {"id": str(gateway.id)},
            },
        ),
        should_cache_fn=bool,
    )
