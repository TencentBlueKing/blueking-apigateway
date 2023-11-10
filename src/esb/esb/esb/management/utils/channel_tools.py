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
from builtins import object

from esb.bkcore.constants import PermissionLevelEnum
from .component_tools import ComponentClient, ConfapiComponentClient


class ChannelClient(object):
    """Channel Tools"""

    def __init__(self, path, channel_config):
        self.path = path
        self.channel_config = channel_config

        if self.channel_config.get("is_confapi"):
            self.comp_client = ConfapiComponentClient(
                self.channel_config, comp_codename=channel_config["comp_codename"]
            )
        else:
            self.comp_client = ComponentClient(self.channel_config, comp_codename=channel_config["comp_codename"])

    def get_info(self):
        info = self.comp_client.get_info()

        is_hidden = self.channel_config.get("is_hidden", False)
        is_deprecated = self.channel_config.get("is_deprecated", False)
        is_public = not (is_hidden or is_deprecated)

        info.update(
            {
                "path": self.path,
                "method": self.channel_config.get("method", ""),
                "comp_codename": self.channel_config["comp_codename"],
                "comp_conf_to_db": self._get_comp_conf_to_db(),
                "config_fields": self.channel_config.get("config_fields"),
                "permission_level": self.channel_config.get("permission_level", PermissionLevelEnum.UNLIMITED.value),
                "verified_user_required": self.channel_config.get("verified_user_required", True),
                "is_public": is_public,
                "no_sdk": self.channel_config.get("no_sdk", None),
            }
        )
        return info

    def _get_comp_conf_to_db(self):
        if self.channel_config.get("comp_conf_to_db"):
            return self.channel_config.get("comp_conf_to_db")

        if self.channel_config.get("comp_conf"):
            return self.channel_config.get("comp_conf")

        if self.channel_config.get("config_fields"):
            return {field["variable"]: field["default"] for field in self.channel_config["config_fields"]}

        return None
