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
from django.test import override_settings

from apigateway.apis.web.api_test.serializers import APITestInputSLZ, AuthorizationSLZ


class TestAuthorizationSLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "bk_app_code": "test",
                    "bk_app_secret": "test",
                },
                {
                    "bk_app_code": "test",
                    "bk_app_secret": "test",
                },
            ),
            (
                {
                    "bk_app_code": "test",
                    "bk_app_secret": "test",
                    "bk_ticket": "",
                    "uin": "",
                },
                {
                    "bk_app_code": "test",
                    "bk_app_secret": "test",
                },
            ),
        ],
    )
    def test_validate(self, params, expected):
        slz = AuthorizationSLZ(data=params)
        slz.is_valid()

        assert dict(slz.validated_data) == expected


class TestAPITestInputSLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "stage_id": 1,
                    "resource_id": 1,
                    "method": "GET",
                    "headers": {},
                    "path_params": {},
                    "query_params": {},
                    "use_test_app": True,
                },
                {
                    "stage_id": 1,
                    "resource_id": 1,
                    "method": "GET",
                    "headers": {},
                    "path_params": {},
                    "query_params": {},
                    "use_test_app": True,
                    "use_user_from_cookies": False,
                    "authorization": {
                        "bk_app_code": "test",
                        "bk_app_secret": "test",
                    },
                },
            ),
            (
                {
                    "stage_id": 1,
                    "resource_id": 1,
                    "method": "GET",
                    "headers": {},
                    "path_params": {},
                    "query_params": {},
                    "use_test_app": False,
                    "authorization": {
                        "bk_app_code": "a1",
                        "bk_app_secret": "s1",
                        "bk_ticket": "t1",
                    },
                },
                {
                    "stage_id": 1,
                    "resource_id": 1,
                    "method": "GET",
                    "headers": {},
                    "path_params": {},
                    "query_params": {},
                    "use_test_app": False,
                    "use_user_from_cookies": False,
                    "authorization": {
                        "bk_app_code": "a1",
                        "bk_app_secret": "s1",
                        "bk_ticket": "t1",
                    },
                },
            ),
        ],
    )
    @override_settings(DEFAULT_TEST_APP={"bk_app_code": "test", "bk_app_secret": "test"})
    def test_validate(self, params, expected):
        slz = APITestInputSLZ(data=params)
        slz.is_valid()

        assert dict(slz.validated_data) == expected
