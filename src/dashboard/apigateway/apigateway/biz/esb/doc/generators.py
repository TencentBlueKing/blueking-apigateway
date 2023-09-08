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
import html
import logging
import textwrap
from abc import ABCMeta
from typing import Optional

from django.utils.translation import gettext
from docutils.core import publish_parts
from pydantic import BaseModel, Field
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.esb.bkcore.models import ComponentDoc, ESBChannel
from apigateway.apps.esb.constants import ComponentDocTypeEnum
from apigateway.biz.esb.board_config import BoardConfig, BoardConfigManager

from .constants import API_URL_PARTS

logger = logging.getLogger(__name__)


class ComponentConfig(BaseModel):
    doc_type: str = Field(default="")
    api_path: str = Field(default="")
    suggest_method: str = Field(default="")


class ComponentDocFactory:
    def __init__(self, board: str, system_name: str, component_name: str):
        self.board = board
        self.system_name = system_name
        self.component_name = component_name

        self.board_config: BoardConfig = BoardConfigManager.get_board_config(self.board)
        self.component: Optional[ESBChannel] = ESBChannel.objects.get_public_component(
            self.board,
            self.system_name,
            self.component_name,
        )
        self.api_doc = self._get_api_doc(self.component)
        self.component_config = self._get_component_config(self.api_doc)

    def get_doc(self) -> Optional[dict]:
        if not (self.api_doc and self.component_config):
            return None

        doc_builder: ComponentDocBuilder
        if self.component_config.doc_type == ComponentDocTypeEnum.RST.value:
            doc_builder = RSTDocBuilder(
                self.board_config,
                self.api_doc.content,
                self.component_config,
            )
        elif self.component_config.doc_type == ComponentDocTypeEnum.MARKDOWN.value:
            doc_builder = MarkdownDocBuilder(
                self.board_config,
                self.api_doc.content,
                self.component_config,
            )
        else:
            raise ValueError(f"unsupported doc_type: {self.component_config.doc_type}")

        return {
            "type": doc_builder.get_doc_type(),
            "content": doc_builder.build_doc(),
            "updated_time": self.api_doc.updated_time,
        }

    def _get_api_doc(self, component: Optional[ESBChannel]) -> Optional[ComponentDoc]:
        if not component:
            return None

        return ComponentDoc.objects.get_api_doc(component.id, language_code=get_current_language_code())

    def _get_component_config(self, api_doc: Optional[ComponentDoc]) -> Optional[ComponentConfig]:
        if not api_doc:
            return None

        doc_configs = api_doc.doc_configs
        if not doc_configs:
            return None

        return ComponentConfig.parse_obj(doc_configs)


class ComponentDocBuilder(metaclass=ABCMeta):
    def __init__(self, board_config: BoardConfig, doc_content: str, component_config: ComponentConfig):
        self.board_config = board_config
        self.doc_content = doc_content
        self.component_config = component_config

    def get_doc_type(self) -> str:
        """获取文档类型"""
        return "unknown"

    def build_doc(self) -> str:
        """构造文档内容"""
        return ""


class MarkdownDocBuilder(ComponentDocBuilder):
    def get_doc_type(self) -> str:
        return ComponentDocTypeEnum.MARKDOWN.value

    def build_doc(self) -> str:
        parts = [
            self._get_api_url_part(),
            self.doc_content,
        ]
        return "\n\n".join(filter(None, parts))

    def _get_api_url_part(self) -> str:
        """API地址部分"""
        # 表头
        part = API_URL_PARTS.get(get_current_language_code(), "")
        part = textwrap.dedent(part).strip()

        # 构造数据部分
        suggest_method = self.component_config.suggest_method
        api_path = self.component_config.api_path

        envs = []
        for env in self.board_config.api_envs:
            if not env.host:
                continue
            envs.append(
                "| {label} | {suggest_method} | {host}{api_path} | {description} |".format(
                    label=gettext(env.label),
                    suggest_method=suggest_method,
                    host=env.host,
                    api_path=api_path,
                    description=gettext(env.description),
                )
            )

        envs_display = "\n".join(envs)
        return f"{part}\n{envs_display}"


class RSTDocBuilder(ComponentDocBuilder):
    def get_doc_type(self) -> str:
        return ComponentDocTypeEnum.HTML.value

    def build_doc(self) -> str:
        parts = [
            self._get_api_url_part(),
            self.doc_content,
        ]
        content = "\n\n".join(filter(None, parts))
        return self._format_rst_to_html(content)

    def _get_api_url_part(self) -> str:
        part = textwrap.dedent(
            """
            API地址
            ~~~~~~~

            """
        )

        suggest_method = self.component_config.suggest_method
        api_path = self.component_config.api_path

        envs = "\n".join(
            [
                (
                    f":{env.label}: \n"
                    f" - 请求方法: {suggest_method}\n"
                    f" - 请求地址: <span>{env.host}{api_path}</span>\n"
                    f" - 备注: {env.description}"
                )
                for env in self.board_config.api_envs
            ]
        )

        return f"{part}\n{envs}"

    def _format_rst_to_html(self, content: str) -> str:
        # 配置 halt_level 为1，让格式错误的rst直接抛出异常
        try:
            doc_html = publish_parts(
                content,
                writer_name="html",
                settings_overrides={
                    "doctitle_xform": False,
                    "initial_header_level": 3,
                    "halt_level": 1,
                },
            )["html_body"]
            return html.unescape(doc_html)
        except Exception:
            logger.exception("unable to convert rst to html, rst: \n%s", content)
            return "unable to convert rst to html"
