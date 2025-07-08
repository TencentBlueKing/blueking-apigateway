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
import datetime
from typing import Optional

from django.utils import timezone

from apigateway.utils.time import NeverExpiresTime, to_datetime_from_now


def calculate_expires(expire_days: Optional[int] = None) -> datetime.datetime:
    # expire_days 为 None 或 0，都表示永久权限
    if expire_days:
        return to_datetime_from_now(days=expire_days)

    return NeverExpiresTime.time


def calculate_renew_time(expire_time: datetime.datetime, expire_days: Optional[int] = None) -> datetime.datetime:
    # 计算续期时间
    #  - 未过期：未过期时间 + 续期时间
    #  - 已过期：当前时间 + 续期时间
    # expire_days 为 None 或 0，都表示永久权限
    if not expire_days:
        return NeverExpiresTime.time

    result = timezone.now()
    if expire_time <= result:
        return result + datetime.timedelta(days=expire_days)
    return expire_time + datetime.timedelta(days=expire_days)
