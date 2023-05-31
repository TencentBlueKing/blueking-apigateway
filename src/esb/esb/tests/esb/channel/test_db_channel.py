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
from ddf import G

from esb.bkcore.models import ESBChannel
from esb.channel.db_channel import DBChannelManager, get_db_channel_manager

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def mock_periodic_timer(mocker):
    mocker.patch(
        "esb.channel.db_channel.PeriodicTimer",
        return_value=mocker.MagicMock(),
    )


class TestDBChannelManager:
    def test_get_channels_from_db(self, mocker):
        G(ESBChannel)

        manager = DBChannelManager()
        channels = manager._get_channels_from_db()
        assert len(channels) >= 1

    def test_refresh_channel_groups(self, mocker):
        mocker.patch.object(
            DBChannelManager,
            "_get_channels_from_db",
            return_value=[
                ("/color/red", {"comp_codename": "generic.color.red"}),
                ("/color/{name}", {"comp_codename": "generic.color.name"}),
            ],
        )
        manager = DBChannelManager()
        manager._refresh_channel_groups()

        assert len(manager.preset_channels) > 0
        assert len(manager.preset_channels_with_path_vars) > 0


def test_get_db_channel_manager():
    m1 = get_db_channel_manager()
    m2 = get_db_channel_manager()

    assert m1 is m2
