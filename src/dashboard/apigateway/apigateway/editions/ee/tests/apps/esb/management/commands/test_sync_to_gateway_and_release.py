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
from django.core.management.base import CommandError

from apigateway.apps.esb.component.constants import ESB_RELEASE_TASK_EXPIRES
from apigateway.apps.esb.management.commands.sync_to_gateway_and_release import Command
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestCommand:
    def test_handle(self, mocker, faker):
        command = Command()
        fake_gateway = G(Gateway)

        # api not exist
        mocker.patch(
            "apigateway.apps.esb.management.commands.sync_to_gateway_and_release.get_esb_gateway",
            side_effect=CommandError("test"),
        )
        with pytest.raises(CommandError):
            command.handle(True)

        # sync
        mock_api = mocker.MagicMock(id=faker.pyint())
        mocker.patch(
            "apigateway.apps.esb.management.commands.sync_to_gateway_and_release.get_esb_gateway",
            return_value=mock_api,
        )
        mock_sync_and_release = mocker.patch(
            "apigateway.apps.esb.management.commands.sync_to_gateway_and_release.sync_and_release_esb_components",
        )
        command.handle(False)
        mock_sync_and_release.called_once_with(mock_api.id, "admin", True)

        # async
        mock_sync_and_release_async = mocker.patch(
            (
                "apigateway.apps.esb.management.commands."
                "sync_to_gateway_and_release.sync_and_release_esb_components.apply_async"
            ),
        )
        command.handle(True)
        mock_sync_and_release_async.asset_called_once_with(
            args=(mock_api.id, "admin", True), expires=ESB_RELEASE_TASK_EXPIRES
        )
