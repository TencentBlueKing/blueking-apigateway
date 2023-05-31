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
from django.test import TestCase

from apigateway.apps.resource.validators import PathVarsValidator


class TestPathVarsValidator(TestCase):
    def test_validate(self):
        data = [
            # ok
            {
                "attrs": {
                    "path": "/",
                },
                "will_error": False,
            },
            # ok
            {
                "attrs": {
                    "path": "/hello/",
                },
                "will_error": False,
            },
            # error, path include invalid char
            {
                "attrs": {"path": "/hello/{username#=}"},
                "will_error": True,
            },
            # error, path include 2 same var
            {
                "attrs": {
                    "path": "/{username}/{username}/",
                },
                "will_error": True,
            },
        ]

        for test in data:
            validator = PathVarsValidator()
            if test.get("will_error"):
                with self.assertRaises(Exception):
                    validator(test["attrs"])
            else:
                validator(test["attrs"])
