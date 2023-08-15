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

from apigateway.apps.esb.management.commands.update_esb_gateway_config import Command
from apigateway.core.constants import GatewayTypeEnum
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestCommand:
    def test_handle(self, mocker):
        command = Command()
        fake_gateway = G(Gateway)

        # api not exist
        mocker.patch(
            "apigateway.apps.esb.management.commands.update_esb_gateway_config.get_esb_gateway",
            side_effect=CommandError("test"),
        )
        with pytest.raises(CommandError):
            command.handle()

        # should not update
        mocker.patch(
            "apigateway.apps.esb.management.commands.update_esb_gateway_config.get_esb_gateway",
            return_value=fake_gateway,
        )
        mock_get_auth_config = mocker.patch(
            (
                "apigateway.apps.esb.management.commands."
                "update_esb_gateway_config.GatewayHandler.get_current_gateway_auth_config"
            ),
            return_value={"api_type": 0, "allow_update_api_auth": False},
        )
        mock_set_auth_config = mocker.patch(
            "apigateway.apps.esb.management.commands.update_esb_gateway_config.GatewayHandler.save_auth_config"
        )
        command.handle()
        mock_set_auth_config.assert_not_called()
        mock_get_auth_config.assert_called_once_with(fake_gateway.id)

        # should update
        mock_get_auth_config = mocker.patch(
            (
                "apigateway.apps.esb.management.commands."
                "update_esb_gateway_config.GatewayHandler.get_current_gateway_auth_config"
            ),
            return_value={"api_type": 10, "allow_update_api_auth": True},
        )
        command.handle()
        mock_set_auth_config.assert_called_once_with(
            fake_gateway.id,
            api_type=GatewayTypeEnum.SUPER_OFFICIAL_API,
            allow_update_api_auth=False,
        )

    @pytest.mark.parametrize(
        "current_config, new_config, expected",
        [
            (
                {
                    "api_type": 10,
                    "allow_update_api_auth": True,
                },
                {
                    "api_type": 10,
                    "allow_update_api_auth": True,
                },
                False,
            ),
            (
                {
                    "api_type": 10,
                    "allow_update_api_auth": True,
                },
                {
                    "api_type": GatewayTypeEnum.CLOUDS_API,
                    "allow_update_api_auth": True,
                },
                False,
            ),
            (
                {
                    "api_type": 10,
                    "allow_update_api_auth": True,
                },
                {
                    "api_type": 0,
                    "allow_update_api_auth": False,
                },
                True,
            ),
            (
                {
                    "api_type": 10,
                    "allow_update_api_auth": True,
                },
                {
                    "api_type": GatewayTypeEnum.OFFICIAL_API,
                    "allow_update_api_auth": False,
                },
                True,
            ),
        ],
    )
    def test_should_update_auth_config(self, current_config, new_config, expected):
        command = Command()
        result = command._should_update_auth_config(current_config, new_config)
        assert result == expected
