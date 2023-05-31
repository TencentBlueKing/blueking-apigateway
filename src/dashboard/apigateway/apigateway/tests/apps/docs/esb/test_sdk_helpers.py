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
from dataclasses import asdict

import pytest

from apigateway.apps.docs.esb.sdk_helpers import DocTemplates, DummyComponentForSDK, NormalComponentForSDK, PythonSDK


class TestPythonSDK:
    def test_as_dict(self):
        config = {
            "board": "open",
            "board_label": "Open",
            "sdk_name": "blueking-component-open",
            "sdk_description": "accss open apis",
            "sdk_version_number": "0.0.1",
            "sdk_download_url": "http://bking.com/blueking-component-open-0.0.1.tar.gz",
            "sdk_install_command": "pip install blueking-component-open",
        }
        sdk = PythonSDK(**config)

        config["language"] = "python"

        assert sdk.as_dict() == config


class TestNormalComponentForSDK:
    def test(self, mock_board):
        component = NormalComponentForSDK(mock_board, "cc", "test")

        assert asdict(component) == {
            "board": mock_board,
            "system_name": "cc",
            "component_name": "test",
            "package_prefix": "blueking.component.open",
        }


class TestDummyComponentForSDK:
    @pytest.mark.parametrize(
        "board_configs, expected",
        [
            (
                {
                    "open": {
                        "name": "open",
                        "label": "Open",
                        "has_sdk": True,
                        "sdk_name": "blueking-component-open",
                        "sdk_package_prefix": "blueking.component.open",
                        "sdk_description": "access open apis",
                    },
                },
                {
                    "board": "open",
                    "system_name": "cc",
                    "component_name": "search_business",
                    "package_prefix": "blueking.component.open",
                },
            ),
            (
                {},
                {
                    "board": "",
                    "system_name": "cc",
                    "component_name": "search_business",
                    "package_prefix": "",
                },
            ),
        ],
    )
    def test(self, settings, board_configs, expected):
        settings.ESB_BOARD_CONFIGS = board_configs

        component = DummyComponentForSDK()

        assert asdict(component) == expected


class TestDocTemplates:
    def test(self, mock_board):
        doc_templates = DocTemplates(mock_board, "en", "python")
        assert doc_templates.templates
