# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from django.test import RequestFactory


@pytest.fixture(scope="class")
def request_factory():
    return RequestFactory()


@pytest.fixture
def fake_request(request_factory):
    return request_factory.get("")


@pytest.fixture
def unique_id():
    return uuid.uuid4().hex


@pytest.fixture
def disable_ttl_cache_tools(mocker):
    mocker.patch("cachetools.ttl.TTLCache.__getitem__", side_effect=KeyError("this is a mock"))
