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
import importlib
from abc import ABCMeta, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Optional

from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.docs.esb.helpers import BoardConfigManager
from apigateway.apps.support.constants import ProgrammingLanguageEnum


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


class SDKFactory:
    @staticmethod
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
        # 不同环境获取 sdk 版本信息的方案可能不同
        module_name, class_name = settings.PYTHON_SDK_MANAGER_CLASS.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)(board)

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


@dataclass
class ComponentForSDK(metaclass=ABCMeta):
    board: str
    system_name: str
    component_name: str
    package_prefix: str = ""

    def __post_init__(self):
        board_config = BoardConfigManager.get_board_config(self.board)
        self.package_prefix = board_config.sdk_package_prefix

    def as_dict(self):
        return asdict(self)


@dataclass
class NormalComponentForSDK(ComponentForSDK):
    pass


@dataclass
class DummyComponentForSDK(ComponentForSDK):
    board: str = ""
    system_name: str = "cc"
    component_name: str = "search_business"
    package_prefix: str = ""

    def __post_init__(self):
        # dummy 数据从 settings 中选取一个 board
        boards = sorted(settings.ESB_BOARD_CONFIGS.keys())
        if not boards:
            return

        self.board = boards[0]
        super().__post_init__()


@dataclass
class DocTemplates:
    board: str
    language_code: str
    programming_language: str
    templates: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.board_config = BoardConfigManager.get_board_config(self.board)
        self.templates = {
            "sdk_usage_example": self._get_sdk_usage_example_template(),
            "sdk_doc": f"esb_sdk/{self.language_code}/{self.programming_language}_sdk_doc.md",
        }

    def _get_sdk_usage_example_template(self):
        template = self.board_config.sdk_doc_templates[f"{self.programming_language}_sdk_usage_example"]
        return f"esb_sdk/{self.language_code}/{template}"
