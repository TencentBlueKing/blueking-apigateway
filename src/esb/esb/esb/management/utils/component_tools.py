# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

import copy
import os
import re
from builtins import object
from importlib import import_module

from django.template import engines
from django.utils import translation
from django.utils.encoding import force_text

from common.base_utils import read_file, smart_unicode
from common.log import logger
from esb.component.base import get_components_manager
from esb.utils.confapis import get_confapis_manager


class ComponentClient(object):
    is_confapi = False

    def __init__(self, channel_conf=None, comp_codename=None, comp_class=None):
        """
        :param comp_codename or comp_class
        """
        self.component_conf = (channel_conf or {}).get("comp_conf") or {}
        self.comp_codename = comp_codename
        self.comp_class = comp_class

        if not self.comp_class:
            self.comp_class = self.get_comp_class(self.comp_codename)

        self.component = self._get_component(self.comp_class, self.component_conf)

        self.system_name = self.get_system_name()
        self.component_name = self.get_component_name()
        self.comp_doc = self.get_comp_doc()

    def __str__(self):
        return "<%s-%s>" % (self.system_name, self.component_name)

    def get_info(self):
        return {
            "system_name": self.system_name,
            "component_name": self.component_name,
            "component_label": self.get_component_label(),
            "component_type": self.get_api_type(),
            "suggest_method": self.get_suggest_method(),
            "doc_md": self.get_comp_doc_md(),
            "is_confapi": self.is_confapi,
            "label_en": self.get_component_label_en(),
        }

    def get_comp_class(self, comp_codename):
        components_manager = get_components_manager()
        comp_class = components_manager.get_comp_by_name(comp_codename)
        if not comp_class:
            raise Exception("Can't find component class of %s" % comp_codename)
        return comp_class

    def _get_component(self, component_cls, component_conf):
        component = component_cls()
        # 对于支持加载自定义配置的组件，调用 setup_conf 方法
        if hasattr(component, "setup_conf") and component_conf:
            component.setup_conf(copy.deepcopy(component_conf))

        return component

    def get_system_name(self):
        return self.component.sys_name

    def get_component_name(self):
        return self.component.get_alias_name()

    def get_api_type(self):
        return self.component.api_type

    def get_component_label(self):
        api_label = getattr(self.component, "label", "")
        if api_label:
            return api_label

        api_label = re.search(r"apiLabel\s*(.+)", self.comp_doc)
        if api_label:
            api_label = api_label.group(1).strip()
        if not api_label:
            return self.component_name

        with translation.override("zh-hans"):
            api_label = engines["jinja2"].from_string(api_label).render()

        return api_label

    def get_component_label_en(self):
        return getattr(self.component, "label_en", "")

    def get_suggest_method(self):
        suggest_method = getattr(self.component, "suggest_method", "")
        if suggest_method:
            return suggest_method.upper()

        api_method = re.search(r"apiMethod\s*(.+)", self.comp_doc)
        if api_method:
            api_method = api_method.group(1).strip()
        if not api_method:
            return ""
        return api_method.upper()

    def get_comp_doc(self):
        return force_text(self.comp_class.__doc__ or "")

    def get_comp_doc_md(self):
        if self.is_comp_doc_md_from_mdfile():
            return self.get_comp_doc_md_from_mdfile()
        else:
            return self.get_comp_doc_md_from_compdoc()

    def get_comp_doc_md_from_compdoc(self):
        with translation.override("en"):
            en_doc = engines["jinja2"].from_string(self.comp_doc).render()

        with translation.override("zh-hans"):
            zh_doc = engines["jinja2"].from_string(self.comp_doc).render()

        return {
            "en": en_doc,
            "zh-hans": zh_doc,
        }

    def is_comp_doc_md_from_mdfile(self):
        apidoc_en_fpath = self._get_apidoc_fpath(language="en")
        apidoc_zhhans_fpath = self._get_apidoc_fpath(language="zh_hans")
        if os.path.isfile(apidoc_en_fpath) or os.path.isfile(apidoc_zhhans_fpath):
            return True
        return False

    def get_comp_doc_md_from_mdfile(self):
        apidoc_en = self._get_apidoc_content(language="en")
        apidoc_zhhans = self._get_apidoc_content(language="zh_hans")
        return {
            "en": smart_unicode(apidoc_en),
            "zh-hans": smart_unicode(apidoc_zhhans),
        }

    def _get_apidoc_content(self, language="en"):
        fpath = self._get_apidoc_fpath(language=language)
        if os.path.isfile(fpath):
            try:
                return read_file(fpath)
            except Exception:
                logger.exception("Read file error. fpath=%s", fpath)
        return ""

    def _get_apidoc_fpath(self, language="en"):
        component_module_path = import_module(self.comp_class.__module__).__file__
        return os.path.join(os.path.dirname(component_module_path), "apidocs", language, "%s.md" % self.component_name)


class ConfapiComponentClient(ComponentClient):
    is_confapi = True

    def __init__(self, channel_conf, comp_codename=None, comp_class=None):
        self.channel_conf = channel_conf
        self.component_conf = self.channel_conf["comp_conf"]
        self.confapis_manager = get_confapis_manager()
        super(ConfapiComponentClient, self).__init__(self.channel_conf, comp_codename, comp_class)

    def get_component_name(self):
        return self.component_conf["name"]

    def get_component_label(self):
        return self.component_conf["label"]

    def get_component_label_en(self):
        return self.component_conf.get("label_en", "")

    def get_suggest_method(self):
        return self.component_conf["suggest_method"].upper()

    def get_api_type(self):
        return self.component_conf.get("api_type") or self.comp_class.api_type

    def get_comp_doc(self):
        return ""

    def get_comp_doc_md(self):
        """
        :return:
        {
            "en": "",
            "zh-hans": "",
        }
        """
        system_name = self.get_system_name().lower()
        component_name = self.get_component_name()
        return self.confapis_manager.get_apidoc(system_name, component_name)
