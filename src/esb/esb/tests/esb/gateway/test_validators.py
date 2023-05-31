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
from common.base_utils import FancyDict
from esb.gateway.validators import APIGatewayAdapter


class TestAPIGatewayAdapter:
    def test_validate(self, mocker, faker):
        adapter = APIGatewayAdapter()

        # enabled false
        request = mocker.MagicMock(apigw=FancyDict(enabled=False), g=FancyDict())
        adapter.validate(request)
        assert dict(request.g) == {}

        # enabled true, has user
        request = mocker.MagicMock(
            apigw=FancyDict(
                enabled=True,
                user={"username": "admin", "verified": True, "valid_error_message": ""},
                app={},
            ),
            g=FancyDict(),
        )
        adapter.validate(request)
        assert dict(request.g) == {
            "current_user_username": "admin",
            "current_user_verified": True,
            "user_valid_error_message": "",
        }

        # enabled true, has app
        request = mocker.MagicMock(
            apigw=FancyDict(
                enabled=True,
                app={"app_code": "my-color", "verified": True, "valid_error_message": ""},
                user={},
            ),
            g=FancyDict(),
        )
        adapter.validate(request)
        assert dict(request.g) == {"app_code": "my-color", "is_app_verified": True, "app_valid_error_message": ""}

        # enabled true, has app and user
        error_message = faker.pystr()
        request = mocker.MagicMock(
            apigw=FancyDict(
                enabled=True,
                app={"app_code": "my-color", "verified": False, "valid_error_message": error_message},
                user={"username": "admin", "verified": False, "valid_error_message": error_message},
            ),
            g=FancyDict(),
        )
        adapter.validate(request)
        assert dict(request.g) == {
            "app_code": "my-color",
            "is_app_verified": False,
            "current_user_username": "admin",
            "current_user_verified": False,
            "user_valid_error_message": error_message,
            "app_valid_error_message": error_message,
        }
