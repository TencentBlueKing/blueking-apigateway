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

from apigateway.apps.monitor.constants import AlarmTypeEnum


@pytest.fixture
def mock_event(mocker, faker):
    return mocker.MagicMock(
        alarm_type=AlarmTypeEnum.APP_REQUEST,
        alarm_record_id=faker.pyint(),
        id=faker.pystr(),
        event_begin_time=faker.date_time(),
        event_create_time=faker.date_time(),
        strategy_id=faker.pyint(),
        alarm_subtype=faker.pystr(),
        event_dimensions={
            "api_id": faker.pyint(),
            "resource_id": faker.pyint(),
            "stage": faker.pystr(),
            "app_code": faker.pystr(),
            "code_name": faker.pystr(),
        },
    )
