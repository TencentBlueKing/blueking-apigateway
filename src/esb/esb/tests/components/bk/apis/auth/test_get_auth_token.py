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
import datetime
from collections import namedtuple

import pytest
from ddf import G

from components.bk.apis.auth.get_auth_token import GetAuthToken
from esb.bkcore.models import AccessToken

pytestmark = pytest.mark.django_db


class TestGetAuthToken:
    def test_get_auth_token(self, unique_id, faker):
        bk_app_code = unique_id
        username = faker.user_name()

        component = GetAuthToken()
        result = component._get_auth_token(bk_app_code, username)
        assert result is None

        token = G(AccessToken, bk_app_code=bk_app_code, user_id=username)
        result = component._get_auth_token(bk_app_code, username)
        assert result == token

    def test_create_auth_token(self, unique_id, faker):
        bk_app_code = unique_id
        username = faker.user_name()

        component = GetAuthToken()
        result = component._create_auth_token(bk_app_code, username)
        assert result is not None

    def test_handle(self, fake_request, unique_id, faker):
        User = namedtuple("User", ["username"])

        fake_request.app_code = unique_id
        username = faker.user_name()

        token = G(
            AccessToken,
            bk_app_code=unique_id,
            user_id=username,
            access_token=unique_id,
            expires=faker.past_datetime(tzinfo=datetime.timezone.utc),
        )
        assert token.has_expired()

        component = GetAuthToken(request=fake_request, current_user=User(username=username))
        result = component.invoke()
        assert result["data"]["auth_token"] != unique_id
        assert result["data"]["username"] == username
        assert result["data"]["expires_in"] > 100 * 24 * 3600
