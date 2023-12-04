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
from abc import ABCMeta, abstractmethod
from dataclasses import asdict, dataclass
from typing import Optional

from cachetools import TTLCache, cached
from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.esb.board_config import BoardConfigManager
from apigateway.common.pypi.pip import PipHelper
from apigateway.common.pypi.registry import SimplePypiRegistry


@dataclass
class PythonSDK:
    board: str
    board_label: str
    sdk_name: str
    sdk_description: str
    sdk_version_number: str
    sdk_download_url: str
    sdk_install_command: str

    def __post_init__(self):
        self.language: str = ProgrammingLanguageEnum.PYTHON.value

    def as_dict(self) -> dict:
        data = asdict(self)
        data["language"] = self.language
        return data


class ESBSDKFetcher:
    @staticmethod
    @cached(cache=TTLCache(maxsize=100, ttl=3600))
    def get_sdk(board: str, language: str) -> Optional[PythonSDK]:
        if language == ProgrammingLanguageEnum.PYTHON.value:
            return PythonSDKManager.get_manager(board).get_sdk()

        raise ValueError(f"unsupported programming language: {language}")


class PythonSDKManager(metaclass=ABCMeta):
    def __init__(self, board: str):
        self.board = board
        self.board_config = BoardConfigManager.get_board_config(self.board)
        self.sdk_name = self.board_config.sdk_name
        self.has_sdk = self.board_config.has_sdk

    @staticmethod
    def get_manager(board: str):
        return SimplePythonSDKManager(board)

    def get_sdk(self) -> Optional[PythonSDK]:
        if not self.has_sdk:
            return None

        return PythonSDK(
            self.board,
            _(self.board_config.label),
            self.sdk_name,
            _(self.board_config.sdk_description),
            self.get_sdk_version_number(),
            self.get_sdk_download_url(),
            self.get_sdk_install_command(),
        )

    @abstractmethod
    def get_sdk_version_number(self) -> str:
        """获取SDK版本号"""

    @abstractmethod
    def get_sdk_download_url(self) -> str:
        """获取SDK下载地址"""

    @abstractmethod
    def get_sdk_install_command(self) -> str:
        """获取SDK安装指令"""


class SimplePythonSDKManager(PythonSDKManager):
    def __init__(self, board: str, index_url: str = ""):
        super().__init__(board)

        self.index_url = index_url or getattr(settings, "PYPI_MIRRORS_REPOSITORY", "")
        self.sdk = self._search_sdk()
        # TODO: 此处重置了父类中 has_sdk 的含义，导致排查问题困难，
        # 此部分考虑需要有SDK 而实际无 sdk 时直接触发异常，或者分两个配置
        self.has_sdk = self.sdk is not None

    def _search_sdk(self):
        if not self.index_url:
            return None

        registry = SimplePypiRegistry(self.index_url)
        return registry.search(self.sdk_name)

    def get_sdk_version_number(self):
        if not self.sdk or not self.sdk.version:
            return ""
        return self.sdk.version

    def get_sdk_download_url(self):
        if not self.sdk:
            return ""
        return self.sdk.url

    def get_sdk_install_command(self):
        helper = PipHelper(extra_index_url=self.index_url)
        return helper.install_command(
            self.sdk_name,
            self.get_sdk_version_number(),
        )
