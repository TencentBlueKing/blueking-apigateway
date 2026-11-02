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
import datetime

import pytest

from apigateway.common.time import calculate_expires, calculate_renew_time
from apigateway.utils.time import NeverExpiresTime

pytestmark = pytest.mark.no_meta_schema


@pytest.fixture
def fixed_now(mocker):
    now = datetime.datetime(2026, 1, 15, 12, tzinfo=datetime.timezone.utc)
    mocker.patch("django.utils.timezone.now", return_value=now)
    return now


@pytest.mark.parametrize("expire_days", [10, 180, None, 0])
def test_calculate_expires(fixed_now, expire_days):
    expected = fixed_now + datetime.timedelta(days=expire_days) if expire_days else NeverExpiresTime.time
    assert calculate_expires(expire_days) == expected


@pytest.mark.parametrize(
    "remaining_days, expire_days, expected_days",
    [(-10, 10, 10), (0, 10, 10), (10, 180, 190), (-10, None, None), (10, None, None), (10, 0, None)],
)
def test_calculate_renew_time(fixed_now, remaining_days, expire_days, expected_days):
    expire_time = fixed_now + datetime.timedelta(days=remaining_days)
    expected = (
        fixed_now + datetime.timedelta(days=expected_days) if expected_days is not None else NeverExpiresTime.time
    )
    assert calculate_renew_time(expire_time, expire_days) == expected
