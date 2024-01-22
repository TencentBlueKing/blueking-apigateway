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
import uuid

import pytest
from ddf import G
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory as DRFAPIRequestFactory

from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.models import Gateway

UserModel = get_user_model()

FAKE_USERNAME = "admin"

# pytest fixtures


class APIRequestFactory(DRFAPIRequestFactory):
    def request(self, *args, **kwargs):
        request = super().request(*args, **kwargs)
        request.user = UserModel(username="admin", is_superuser=True)
        request.COOKIES[settings.BK_LOGIN_TICKET_KEY] = "access_token"
        return request


@pytest.fixture(scope="class")
def request_factory():
    return APIRequestFactory()


@pytest.fixture
def unique_id():
    return uuid.uuid4().hex


@pytest.fixture
def fake_gateway(faker):
    gateway = G(
        Gateway,
        name=faker.pystr(),
        _maintainers=FAKE_USERNAME,
        status=1,
        is_public=True,
    )

    GatewayAuthContext().save(gateway.pk, {})

    return gateway
