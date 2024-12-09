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
import json
from dataclasses import dataclass

from dateutil.tz import tzutc
from django.contrib.auth import get_user_model
from django_dynamic_fixture import G
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory as DRFAPIRequestFactory

from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway

UserModel = get_user_model()


class APIRequestFactory(DRFAPIRequestFactory):
    def request(self, *args, **kwargs):
        request = super().request(*args, **kwargs)
        request.user = create_user()
        return request


def create_user(username="admin"):
    return UserModel(username=username)


def create_gateway(**defaults):
    user = create_user()
    data = {
        "created_by": user.username,
        "_maintainers": user.username,
        "status": GatewayStatusEnum.ACTIVE.value,
        "tenant_mode": "single",
        "tenant_id": "default",
        "is_public": True,
    }
    data.update(defaults)
    return G(Gateway, **data)


def get_response_json(response):
    if isinstance(response, Response):
        response.render()
    return json.loads(response.content)


def create_request():
    factory = APIRequestFactory()
    return factory.get("/")


@dataclass
class DummyTime:
    time: datetime.datetime
    str: str
    timestamp: int


dummy_time = DummyTime(
    time=datetime.datetime(2019, 1, 1, 12, 30, tzinfo=tzutc()),
    str="2019-01-01 20:30:00",
    timestamp=1546345800,
)
