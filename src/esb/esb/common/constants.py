# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from enum import Enum

from common.base_utils import FancyDict

COMPONENT_STATUSES = FancyDict(
    (
        ("ARGUMENT_ERROR", 0),
        ("PENDING", 1),
        ("EXECUTING", 2),
        ("SUCCESS", 3),
        ("FAILURE", 4),
        ("EXCEPTION", 5),
        ("UNABLE_TO_CYCLE", 6),
        ("PENDING_TOO_LONG", 7),
    )
)


API_TYPE_OP = "operate"
API_TYPE_Q = "query"

HTTP_METHOD = FancyDict(
    (
        ("GET", "GET"),
        ("POST", "POST"),
    )
)


class CacheTimeLevel(Enum):

    CACHE_TIME_SHORT = 5 * 60
    CACHE_TIME_MEDIUM = 3600
    CACHE_TIME_LONG = 24 * 3600


CACHE_MAXSIZE = 2000


class FunctionControllerCodeEnum(Enum):

    SKIP_USER_AUTH = "user_auth::skip_user_auth"
    JWT_KEY = "jwt::private_public_key"
