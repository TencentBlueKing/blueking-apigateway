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
from typing import List

from django.conf import settings
from django.utils.translation import gettext
from pydantic import BaseModel, Field


class APIEnv(BaseModel):
    name: str
    label: str
    host: str
    description: str = ""


class BoardConfig(BaseModel):
    name: str
    label: str
    api_envs: List[APIEnv] = Field(default_factory=list)
    has_sdk: bool = False
    sdk_name: str = ""
    sdk_package_prefix: str = ""
    sdk_description: str = ""
    sdk_doc_templates: dict = Field(default_factory=dict)


class BoardConfigManager:
    @staticmethod
    def get_board_config(board: str) -> BoardConfig:
        return BoardConfig.model_validate(settings.ESB_BOARD_CONFIGS[board])

    @classmethod
    def get_board_label(cls, board: str) -> str:
        config = cls.get_board_config(board)
        return gettext(config.label)
