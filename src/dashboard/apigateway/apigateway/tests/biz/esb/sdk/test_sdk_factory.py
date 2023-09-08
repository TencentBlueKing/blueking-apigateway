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

from apigateway.biz.esb.board_config import BoardConfig
from apigateway.biz.esb.sdk.sdk_factory import PythonSDK, SimplePythonSDKManager


@pytest.fixture()
def index_url(faker):
    return faker.url()


@pytest.fixture()
def board(settings, faker):
    board = faker.pystr()
    settings.ESB_BOARD_CONFIGS[board] = BoardConfig(
        name=faker.pystr(),
        label=faker.pystr(),
        sdk_name=faker.pystr(),
    ).dict()
    return board


@pytest.fixture()
def pypi_registry(mocker):
    cls = mocker.MagicMock()
    mocker.patch("apigateway.biz.esb.sdk.sdk_factory.SimplePypiRegistry", cls)
    return cls.return_value


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


class TestSimplePythonSDKManager:
    def test_sdk_not_found(self, board, index_url, pypi_registry):
        pypi_registry.search.return_value = None

        manager = SimplePythonSDKManager(board, index_url)

        assert manager.get_sdk() is None

    def test_sdk_found(self, board, index_url, pypi_registry, mocker, faker):
        package = mocker.MagicMock(
            version=faker.pystr(),
            url=faker.pystr(),
        )
        pypi_registry.search.return_value = package

        manager = SimplePythonSDKManager(board, index_url)

        sdk = manager.get_sdk()
        assert sdk is not None
        assert sdk.board == board
        assert sdk.sdk_name == manager.sdk_name
        assert sdk.sdk_version_number == package.version
        assert sdk.sdk_download_url == package.url
        assert sdk.sdk_install_command != ""
