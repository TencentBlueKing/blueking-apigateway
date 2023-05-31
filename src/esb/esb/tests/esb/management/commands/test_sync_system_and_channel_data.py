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

from esb.bkcore.models import ESBChannel, System
from esb.management.commands.sync_system_and_channel_data import Command

pytestmark = pytest.mark.django_db


class TestCommand:
    def test_update_channels(self, mocker, unique_id):
        system_name = unique_id
        channel_method = "GET"
        channel_path_exist = "/%s/exist/" % unique_id
        channel_path_not_exist = "/%s/not-exist/" % unique_id

        mocker.patch(
            "esb.management.commands.sync_system_and_channel_data.conf_tools.ConfClient",
            return_value=mocker.MagicMock(
                channels={
                    system_name: [
                        {
                            "method": channel_method,
                            "path": channel_path_exist,
                            "comp_codename": "generic.test_system.test",
                            "comp_conf_to_db": {},
                            "system_name": "test_system",
                            "component_name": "test",
                            "component_label": "test",
                            "component_type": "query",
                            "suggest_method": "GET",
                            "permission_level": "unlimited",
                            "verified_user_required": True,
                            "is_public": True,
                            "is_confapi": False,
                        },
                        {
                            "method": channel_method,
                            "path": channel_path_not_exist,
                            "comp_codename": "generic.test_system.test",
                            "comp_conf_to_db": {},
                            "system_name": "test_system",
                            "component_name": "test",
                            "component_label": "test",
                            "component_type": "query",
                            "suggest_method": "GET",
                            "permission_level": "normal",
                            "verified_user_required": False,
                            "is_public": True,
                            "is_confapi": False,
                        },
                    ]
                },
            ),
        )

        system = G(System, name=system_name)

        channel_1 = G(ESBChannel, system=system, is_public=False, method=channel_method, path=channel_path_exist)
        channel_2 = G(ESBChannel, system=system, is_public=True)

        mocker.patch.object(
            Command,
            "_get_official_channel_ids",
            return_value=[channel_1.id, channel_2.id],
        )

        command = Command()
        command.force = False
        command.update_channels()

        # created
        assert ESBChannel.objects.get(method=channel_method, path=channel_path_not_exist).is_public
        # changed
        assert ESBChannel.objects.get(id=channel_1.id).is_public
        # not specified
        assert not ESBChannel.objects.get(id=channel_2.id).is_public

    def test_get_official_channel_ids(self, mocker, unique_id):
        system = G(System, name=unique_id)
        channel = G(ESBChannel, system=system)

        mocker.patch(
            "esb.management.commands.sync_system_and_channel_data.System.objects.get_official_ids",
            return_value=[system.id],
        )

        assert Command()._get_official_channel_ids() == [channel.id]

    def test_hide_channels(self):
        channel = G(ESBChannel, is_public=True)

        Command()._hide_channels([channel.id])

        assert not ESBChannel.objects.get(id=channel.id).is_public
