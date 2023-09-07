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

from apigateway.biz.esb.board_config import BoardConfigManager


class TestBoardConfigManager:
    @pytest.mark.parametrize(
        "board_configs, board, expected",
        [
            (
                {
                    "open": {
                        "name": "open",
                        "label": "Open",
                        "api_envs": [
                            {
                                "name": "prod",
                                "label": "正式环境",
                                "host": "http://bking.com",
                                "description": "访问后端正式环境",
                            },
                        ],
                        "has_sdk": True,
                        "sdk_name": "blueking-component-open",
                        "sdk_package_prefix": "blueking.component.open",
                        "sdk_description": "access open apis",
                        "sdk_doc_templates": {},
                    },
                },
                "open",
                {
                    "name": "open",
                    "label": "Open",
                    "api_envs": [
                        {
                            "name": "prod",
                            "label": "正式环境",
                            "host": "http://bking.com",
                            "description": "访问后端正式环境",
                        },
                    ],
                    "has_sdk": True,
                    "sdk_name": "blueking-component-open",
                    "sdk_description": "access open apis",
                    "sdk_package_prefix": "blueking.component.open",
                    "sdk_doc_templates": {},
                },
            ),
        ],
    )
    def test_get_board_config(
        self,
        settings,
        board_configs,
        board,
        expected,
    ):
        settings.ESB_BOARD_CONFIGS = board_configs
        board_config = BoardConfigManager.get_board_config(board)

        assert board_config.dict() == expected

    @pytest.mark.parametrize(
        "board_configs, board, expected",
        [
            (
                {
                    "open": {
                        "name": "open",
                        "label": "Open",
                    },
                },
                "open",
                "Open",
            )
        ],
    )
    def test_get_board_label(self, settings, board_configs, board, expected):
        settings.ESB_BOARD_CONFIGS = board_configs

        result = BoardConfigManager.get_board_label(board)
        assert result == expected
