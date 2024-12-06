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

from apigateway.apps.esb.helpers import BoardConfigManager


class TestBoardConfigManager:
    @pytest.fixture
    def mock_board_configs(self):
        return {
            "default": {
                "name": "default",
                "label": "test",
                "should_display_label": False,
            }
        }

    @pytest.mark.parametrize(
        "board, expected",
        [
            (
                "default",
                {
                    "name": "default",
                    "label": "test",
                    "should_display_label": False,
                },
            )
        ],
    )
    def test_get_board_config(self, mocker, mock_board_configs, board, expected):
        mocker.patch(
            "apigateway.apps.esb.helpers.get_esb_board_config",
            return_value=mock_board_configs[board],
        )

        board_config = BoardConfigManager.get_board_config(board)
        assert board_config.model_dump() == expected

    @pytest.mark.parametrize(
        "should_display_label, board, expected",
        [
            (
                False,
                "default",
                "",
            ),
            (
                True,
                "default",
                "test",
            ),
        ],
    )
    def test_get_optional_display_label(self, mocker, mock_board_configs, should_display_label, board, expected):
        mock_board_configs[board]["should_display_label"] = should_display_label
        mocker.patch(
            "apigateway.apps.esb.helpers.get_esb_board_config",
            return_value=mock_board_configs[board],
        )

        result = BoardConfigManager.get_optional_display_label(board)
        assert result == expected
