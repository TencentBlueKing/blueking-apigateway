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

import logging
import os
from importlib import import_module

from components.constants import BK_SYSTEMS, SYSTEM_DOC_CATEGORY
from components.esb_conf import CUSTOM_APIS_REL_PATH
from esb.utils import fpath_to_module
from esb.utils.confapis import get_confapis_manager
from esb.utils.esb_config import EsbConfigParser

from .channel_tools import ChannelClient

logger = logging.getLogger(__name__)


class ConfClient:
    def __init__(self):
        self.custom_conf_module = self._get_custom_conf_module()

    @property
    def system_doc_category(self):
        return self.default_system_doc_category + self.custom_system_doc_category

    @property
    def systems(self):
        return self.default_systems + self.custom_systems

    @property
    def channels(self):
        all_channels = self.default_channels

        for system_name, system_channels in list(self.custom_channels.items()):
            all_channels.setdefault(system_name, [])
            all_channels[system_name].extend(system_channels)

        for system_name, system_channels in list(self.confapis_channels.items()):
            all_channels.setdefault(system_name, [])
            all_channels[system_name].extend(system_channels)

        return all_channels

    @property
    def buffet_components(self):
        return self.default_buffet_components + self.custom_buffet_components

    @property
    def default_system_doc_category(self):
        return SYSTEM_DOC_CATEGORY

    @property
    def default_systems(self):
        return list(BK_SYSTEMS.values())

    @property
    def default_channels(self):
        return self._get_channels_by_config(self._default_channels_conf)

    @property
    def default_buffet_components(self):
        return []

    @property
    def custom_system_doc_category(self):
        return getattr(self.custom_conf_module, "SYSTEM_DOC_CATEGORY", [])

    @property
    def custom_systems(self):
        return getattr(self.custom_conf_module, "SYSTEMS", [])

    @property
    def custom_channels(self):
        return self._get_channels_by_config(self._custom_channels_conf)

    @property
    def confapis_channels(self):
        return self._get_channels_by_config(self._confapis_channels_conf)

    @property
    def custom_buffet_components(self):
        return getattr(self.custom_conf_module, "BUFFET_COMPONENTS", [])

    @property
    def _default_channels_conf(self):
        """
        :return
        [
            ("/cc/get_host/", {"comp_codename": "generic.cc.get_host"}),
        ]
        """
        return EsbConfigParser().get_channels()

    @property
    def _custom_channels_conf(self):
        return [
            (channel["path"], {"comp_codename": channel["comp_codename"]}) if isinstance(channel, dict) else channel
            for channel in getattr(self.custom_conf_module, "CHANNELS", [])
        ]

    @property
    def _confapis_channels_conf(self):
        confapis_manager = get_confapis_manager()
        confapis_channels_conf = confapis_manager.get_apis_conf()
        # check if channel is existed in default channels
        default_channel_path_list = [channel[0] for channel in self._default_channels_conf]
        confapi_channel_path_list = []
        _channels_conf = []
        for path, value in confapis_channels_conf:
            channel_key = "%s:%s" % (path, value.get("method", ""))
            if path in default_channel_path_list:
                logger.warning("confapi channel [path=%s] exists in esb_conf.py, will be ignored", path)
                continue
            if channel_key in confapi_channel_path_list:
                logger.warning("confapi channel [path=%s] is duplicate, will be ignored", path)
                continue
            confapi_channel_path_list.append(channel_key)
            _channels_conf.append((path, value))
        return _channels_conf

    def _get_custom_conf_module(self):
        conf_path = os.path.join(CUSTOM_APIS_REL_PATH, "conf.py")
        try:
            return import_module(fpath_to_module(conf_path))
        except Exception:
            return None

    def _get_channels_by_config(self, channels_config):
        """
        :return:
        {
            "CC": [
                {
                    "path": "/cc/get_host/",
                    "comp_codename": "generic.cc.get_host",
                    "comp_conf_to_db": {},
                    "config_fields": [],
                    "system_name": "CC",
                    "component_name": "get_host",
                    "component_label": "Get host",
                    "component_type": "query",
                    "suggest_method": "GET",
                    "verified_user_required": False,
                    "permission_level": "unlimited",
                    "is_public": False,
                    "is_confapi": False,
                }
            ]
        }
        """
        channels = {}
        for path, value in channels_config:
            try:
                channel_client = ChannelClient(path, value)
                api_info = channel_client.get_info()
            except Exception:
                logger.exception("channel get api data fail, path=%s, value=%s", path, value)
                continue

            system_name = api_info["system_name"]
            channels.setdefault(system_name, [])
            channels[system_name].append(api_info)
        return channels
