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
import pytest


@pytest.fixture
def fake_release_data(mocker, fake_gateway, fake_stage):
    """Create a fake release data object for testing"""
    release_data = mocker.Mock()
    release_data.gateway = fake_gateway
    release_data.stage = fake_stage
    release_data.get_stage_backend_configs = mocker.Mock(return_value={})
    release_data.get_stage_plugins = mocker.Mock(return_value=[])
    release_data.jwt_private_key = "test-jwt-key"
    release_data.gateway_auth_config = {}
    return release_data
