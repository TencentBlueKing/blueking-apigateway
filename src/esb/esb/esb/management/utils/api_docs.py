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

import json
import logging
import re
import textwrap
from builtins import object

import markdown
from django.template import engines
from django.utils import translation

from common.base_utils import get_md5, smart_unicode
from esb.bkcore.models import ComponentDoc
from esb.management.utils import component_tools
from esb.utils.esb_config import EsbConfigParser

logger = logging.getLogger(__name__)


class ApiDocManager(object):
    def __init__(self, is_update_all_api_doc=False):
        self.is_update_all_api_doc = is_update_all_api_doc
        self.all_doc_md_md5 = self.get_all_doc_md_md5()

    def get_api_doc(self, channel):
        api_doc = APIDoc(channel)
        api_doc_info = api_doc.get_doc_info()

        old_doc_md_md5 = self.get_old_doc_md5(channel.id)
        if not (self.is_update_all_api_doc or api_doc._is_doc_changed(old_doc_md_md5)):
            raise DocNotChangedException
        return api_doc_info

    def get_old_doc_md5(self, path):
        return self.all_doc_md_md5.get(path)

    def get_all_doc_md_md5(self):
        return dict(ComponentDoc.objects.values_list("component_id", "content_md5"))


API_PATH = """
### {{ _("请求地址") }}

{{ api_path }}

"""

API_METHOD = """
### {{ _("请求方法") }}

{{ api_method }}

"""


class APIDoc(object):
    def __init__(self, channel):
        self.jinja2_engine = engines["jinja2"]

        self.channel = channel
        self.api_path = self.channel.api_path
        self.api_data = self.get_api_data()

        self._update_doc_md()
        self.raw_doc_md_md5 = self._get_raw_doc_md_md5()

    def get_doc_info(self):
        return {
            "doc_md": self.doc_md,
            "doc_html": self._get_doc_html(),
            # 用于计算原始文档的 md5
            "raw_doc_md_md5": self.raw_doc_md_md5,
            "system_name": self.api_data["system_name"],
            "component_name": self.api_data["component_name"],
        }

    def get_api_data(self):
        channel_conf = self._get_channel_conf()
        if self.channel.is_confapi:
            component_client = component_tools.ConfapiComponentClient(
                channel_conf, comp_codename=self.channel.component_codename
            )
        else:
            component_client = component_tools.ComponentClient(
                channel_conf, comp_codename=self.channel.component_codename
            )
        return component_client.get_info()

    def _get_channel_conf(self):
        return {
            "comp_codename": self.channel.component_codename,
            "comp_conf": {
                "name": self.channel.name,
                "label": self.channel.description,
                "suggest_method": self.channel.method or self.channel.config.get("suggest_method", ""),
            },
        }

    def _get_doc_html(self):
        doc_html = {}
        for language, _doc_md in list(self.doc_md.items()):
            doc_html[language] = self._format_md_to_html(_doc_md)
        return doc_html

    def _get_raw_doc_md_md5(self):
        return get_md5(json.dumps(self.doc_md))

    def _is_doc_changed(self, old_doc_md_md5):
        return old_doc_md_md5 != self.raw_doc_md_md5

    def _update_doc_md(self):
        doc_md = {}
        for language, _doc_md in list(self.api_data["doc_md"].items()):
            with translation.override(language):
                _doc_md_parts = [
                    smart_unicode(self._get_api_method_part()),
                    smart_unicode(self._get_url_part()),
                    smart_unicode(self._get_doc_common_args_part()),
                    "\n",
                    smart_unicode(self._format_origin_document(_doc_md)),
                ]
                doc_md[language] = "\n".join(_doc_md_parts)

        self.doc_md = doc_md

    def _format_origin_document(self, document):
        """格式化原始文档

        不要使用 Jinja2 模板渲染，因其中内容可能与 Jinja2 模板冲突
        """
        formated_document = document

        formated_document = textwrap.dedent(formated_document).strip()

        # 将文档中 `{{ common_args_desc }}` 替换为空，公共参数拼接到开头，不需要再写到原始文档中
        formated_document = re.sub(r"{{ *common_args_desc *}}", "", formated_document)

        # 去除文档中 apiMethod 和 apiLabel 的标记
        formated_document = self._clear_api_flag(formated_document)

        return formated_document

    def _get_url_part(self):
        return self._format(API_PATH, {"api_path": self.api_path})

    def _get_api_method_part(self):
        api_method = self.api_data["suggest_method"].upper()
        if not api_method:
            return ""
        return self._format(API_METHOD, {"api_method": api_method})

    def _get_doc_common_args_part(self):
        doc_common_args = EsbConfigParser().get_doc_common_args()
        part = self._format(doc_common_args, {}).replace("&gt;", ">")
        return textwrap.dedent(part)

    def _clear_api_flag(self, document):
        lines = document.splitlines()
        for index, line in enumerate(lines):
            # 部分组件使用组件类的 docstring 管理组件文档，
            # 此类文档中，文档开头的 apiMethod、apiLabel 用于描述组件的一些属性，不属于文档内容，需去除，
            # 用 apiMethod、apiLabel 描述组件属性的方案，已不推荐使用
            if line.startswith("api"):
                lines[index] = ""
            else:
                break
        return "\n".join(lines).strip()

    def _format_md_to_html(self, doc_md):
        doc_html = markdown.markdown(
            doc_md,
            extensions=["tables", "attr_list", "fenced_code", "smarty", "codehilite", "toc"],
        )
        return doc_html

    def _format(self, content, context):
        return self.jinja2_engine.from_string(content).render(context=context)


class DocNotChangedException(Exception):
    pass
