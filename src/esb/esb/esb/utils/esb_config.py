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
from typing import List, Optional

from esb.utils import config


class EsbConfigParser:
    def __init__(self):
        self.esb_config = config.ESB_CONFIG["config"]

    def get_default_channel_classes(self):
        """
        :return:
        {
            "api": ApiChannelForAPIS
        }
        """
        default_channel_classes = self.esb_config.get("default_channel_classes")
        if default_channel_classes:
            return default_channel_classes

        return self.esb_config["channel_groups"].get("default", {}).get("channel_classes")

    def get_rewrite_channels(self):
        """
        :return:
        {
            "/v2/cmsi/send_voice_msg/": "/cmsi/send_voice_msg/",
        }
        """
        rewrite_channels = {}
        channel_groups = self.esb_config["channel_groups"]
        for group_name in channel_groups.keys():
            rewrite_channels.update(channel_groups[group_name].get("rewrite_channels", {}))
        return rewrite_channels

    def get_channels(self):
        """
        :return:
        [
            ("/cc/get_host/", {"comp_codename": "generic.cc.get_host"}),
        ]
        """
        channels = []
        for channel_group in self.esb_config["channel_groups"].values():
            channels.extend(channel_group["preset_channels"])
        return channels

    def get_channels_mapping(self):
        """
        :return:
        {
            ":/echo/": {
                "comp_codename": "generic.echo.echo",
                "is_hidden": False,
                "is_deprecated": False,
                "request_validators": [],
                "channel_path": "/echo/",
                "channel_classes": {"api": ApiChannelForAPIS},
                "config_fields": [],
                "comp_conf": {
                    "name": "echo",
                }
            }
        }
        """
        mapping = {}
        for channel_group in self.esb_config["channel_groups"].values():
            channel_classes = channel_group["channel_classes"]
            for path, value in channel_group["preset_channels"]:
                channel_key = self.get_channel_key(value.get("method"), path)
                mapping[channel_key] = dict(
                    value,
                    channel_path=path,
                    channel_classes=channel_classes,
                )

        return mapping

    def get_channel_key(self, method: Optional[str], path: str) -> str:
        return f"{method or ''}:{path}"

    def get_doc_common_args(self) -> str:
        return self.esb_config.get("doc_common_args") or ""

    def get_component_groups(self) -> List[dict]:
        return self.esb_config.get("component_groups") or []
