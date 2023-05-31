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
import json
from unittest import mock

from apigateway.account.middlewares import SelfAppCodeAppSecretLoginMiddleware


class TestSelfAppCodeAppSecretLoginMiddleware:
    def test_call(self, fake_request, settings):
        settings.BK_APP_CODE = "app-code"
        settings.BK_APP_SECRET = "app-secret"

        def get_response(request):
            return request

        middleware = SelfAppCodeAppSecretLoginMiddleware(get_response)

        fake_request.META = {}
        middleware(fake_request)
        assert not hasattr(fake_request, "app")

        fake_request.META = {
            "HTTP_X_BKAPI_AUTHORIZATION": json.dumps(
                {
                    "bk_app_code": settings.BK_APP_CODE,
                    "bk_app_secret": settings.BK_APP_SECRET,
                }
            )
        }
        fake_request.user = mock.MagicMock(is_authenticated=False)
        middleware(fake_request)
        assert fake_request.app.app_code == settings.BK_APP_CODE
        assert fake_request.user.username == ""
