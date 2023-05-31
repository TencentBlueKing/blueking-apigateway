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
from django.utils.encoding import force_str


class Matcher:
    """计算条件匹配"""

    def __init__(self):
        self.match_function = MatchFunction()

    def is_match(self, data, conditions):
        """
        判断数据是否与条件匹配，至少与 condition 中一项规则匹配，则认为数据匹配
        :param data: 待判断的数据
            {
                "error": "error"
            }
        :param conditions: 判断条件
        [
            [
                {
                    "field": "error",
                    "method": "eq",
                    "value": "error"
                }
            ]
        ]
        """
        if not conditions:
            return False
        return self.evaluate(data, conditions)

    def evaluate(self, data, conditions):
        """只要有一项条件匹配，即认为数据匹配"""
        for condition in conditions:
            if self.evaluate_with_and(data, condition):
                return True
        return False

    def evaluate_with_and(self, data, condition):
        """评估数据是否匹配，condition 中的所有条件都满足，则认为匹配"""
        for item in condition:
            field = item.get("field")
            method = item.get("method")
            value = item.get("value")

            if not all([field, method, value]):
                continue

            data_value = data.get(field, "")
            if not self.match_function.operate(method, data_value, value):
                return False

        return True


class MatchFunction:
    def operate(self, method, data_value, condition_value):
        return getattr(self, f"_{method}")(data_value, condition_value)

    def _in(self, data_value, condition_value):
        if not isinstance(condition_value, list):
            raise ValueError(f"condition value must be list for method [in], value={condition_value}")

        return data_value in condition_value

    def _include(self, data_value, condition_value):
        if not data_value:
            return False

        if isinstance(condition_value, list):
            for cond_value in condition_value:
                if cond_value in data_value:
                    return True
            return False

        return condition_value in data_value

    def _eq(self, data_value, condition_value):
        if condition_value == "*":
            return True
        return data_value == condition_value

    def _startswith(self, data_value, condition_value):
        data_value = force_str(data_value)
        condition_value = force_str(condition_value)
        return data_value.startswith(condition_value)
