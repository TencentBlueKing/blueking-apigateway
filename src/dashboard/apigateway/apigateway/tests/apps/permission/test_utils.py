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
import pytest

from apigateway.apps.permission.utils import calculate_expires
from apigateway.utils.time import now_datetime


@pytest.mark.parametrize(
    "expire_days, expected",
    [
        (10, 10),
        (180, 180),
        (None, 360 * 10),
    ],
)
def test_calculate_expires(expire_days, expected):
    result = calculate_expires(expire_days)
    # 因时间创建的误差，因此，结尾时间减去 2 秒
    assert (result - now_datetime()).total_seconds() >= expected * 24 * 3600 - 2
