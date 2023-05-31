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
from django.conf import settings
from pydantic import BaseModel

from apigateway.apps.esb.constants import get_esb_board_config


class BoardConfig(BaseModel):
    name: str
    label: str
    should_display_label: bool

    @property
    def optional_display_label(self) -> str:
        if self.should_display_label:
            return self.label
        return ""


class BoardConfigManager:
    @classmethod
    def get_board_config(cls, board: str) -> BoardConfig:
        return BoardConfig.parse_obj(get_esb_board_config(board))

    @classmethod
    def get_optional_display_label(cls, board: str) -> str:
        config = cls.get_board_config(board)
        return config.optional_display_label


def get_component_doc_link(board: str, system_name: str, component_name: str) -> str:
    return settings.COMPONENT_DOC_URL_TMPL.format(
        board=board,
        system_name=system_name,
        component_name=component_name,
    )
