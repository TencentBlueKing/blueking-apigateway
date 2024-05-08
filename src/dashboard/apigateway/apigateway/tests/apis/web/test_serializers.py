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
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.serializers import BaseBackendConfigSLZ


class TestBaseBackendConfigSLZ:
    @pytest.mark.parametrize(
        "data, will_raise",
        [
            (
                {
                    "type": "node",
                    "timeout": {"connect": 1, "read": 1, "send": 1},
                    "loadbalance": "chash",
                    "hosts": [{"scheme": "http", "host": "test.com", "weight": 1}],
                    "hash_on": "test",
                    "key": "test",
                },
                True,
            ),
            (
                {
                    "type": "node",
                    "timeout": {"connect": 1, "read": 1, "send": 1},
                    "loadbalance": "chash",
                    "hosts": [{"scheme": "http", "host": "test.com", "weight": 1}],
                    "hash_on": "vars",
                    "key": "test",
                },
                True,
            ),
            (
                {
                    "type": "node",
                    "timeout": {"connect": 1, "read": 1, "send": 1},
                    "loadbalance": "chash",
                    "hosts": [{"scheme": "http", "host": "test.com", "weight": 1}],
                    "hash_on": "vars",
                    "key": "uri",
                },
                False,
            ),
            (
                {
                    "type": "node",
                    "timeout": {"connect": 1, "read": 1, "send": 1},
                    "loadbalance": "chash",
                    "hosts": [{"scheme": "http", "host": "test.com", "weight": 1}],
                    "hash_on": "header",
                    "key": "test",
                },
                False,
            ),
        ],
    )
    def test_valid_loadbalance(self, data, will_raise):
        if will_raise:
            with pytest.raises(ValidationError):
                slz = BaseBackendConfigSLZ(data=data)
                slz.is_valid(raise_exception=True)

        else:
            slz = BaseBackendConfigSLZ(data=data)
            slz.is_valid(raise_exception=False)
