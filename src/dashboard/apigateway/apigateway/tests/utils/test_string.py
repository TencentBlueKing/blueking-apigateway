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
import unittest

from apigateway.utils.string import random_string, truncate_string


class TestUtilsString(unittest.TestCase):
    def test_truncate_string(self):
        s = "helloworld"
        length = len(s)

        self.assertEqual(truncate_string(s, 5), "hello")
        self.assertEqual(truncate_string(s, length), s)
        self.assertEqual(truncate_string(s, length + 1), s)

        self.assertEqual(truncate_string(s, 8, "..."), "hello...")

    def test_random_string(self):
        self.assertEqual(len(random_string()), 10)
        self.assertEqual(len(random_string(5)), 5)

        self.assertTrue(random_string().isalpha())
