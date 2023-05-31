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
from typing import List, Tuple

from django.conf import settings

from common.singleton import SingletonMeta
from esb.bkcore.models import ESBChannel, System
from esb.channel.base import BaseChannelManager
from esb.utils.esb_config import EsbConfigParser
from esb.utils.thread import PeriodicTimer


class DBChannelManager(BaseChannelManager, metaclass=SingletonMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._esb_config_parser = EsbConfigParser()
        self._esb_channels_mapping = self._esb_config_parser.get_channels_mapping()

        self.set_default_channel_classes(self._esb_config_parser.get_default_channel_classes())

        # rewrite_channels 属于 esb_conf 配置，但是 esb_conf 中的 channel 已全部写入 db，
        # 为不单独处理 rewrite_channels, 因此将其配置到此处
        self.update_rewrite_channels(self._esb_config_parser.get_rewrite_channels())

        # 初始化数据，防止第一次请求时无数据
        self._refresh_channel_groups()

        self._refresh_channel_timer = PeriodicTimer(settings.DB_CHANNEL_REFRESH_INTERVAL, self._refresh_channel_groups)
        self._refresh_channel_timer.start()

    def __str__(self):
        return "<DBChannelManager>"

    def _refresh_channel_groups(self):
        # 刷新 db channel 时，加载的数据应与 db 中数据保持一致，
        # 并且应在生成数据后，再替换 `preset_channels`，防止因生成过程中部分数据未加载导致请求出错
        channels = self._get_channels_from_db()

        preset_channels, preset_channels_with_path_vars = self._generate_channel_groups(
            self.get_default_channel_classes(),
            channels,
        )

        self.preset_channels = preset_channels
        self.preset_channels_with_path_vars = preset_channels_with_path_vars

    def _get_channels_from_db(self) -> List[Tuple[str, dict]]:
        system_id_to_timeout = System.objects.get_system_id_to_timeout()

        channels = []
        for channel in ESBChannel.objects.all():
            value = {
                "comp_codename": channel.component_codename,
                "method": channel.method,
                "is_active": channel.is_active,
                "comp_conf": channel.config,
                "channel_conf": channel.channel_conf,
                "timeout": channel.get_real_timeout(system_id_to_timeout.get(channel.system_id)),
            }

            # 复用 esb_conf 中的  validators 和 channel_classes
            channel_key = self._esb_config_parser.get_channel_key(channel.method, channel.path)
            channel_from_config = self._esb_channels_mapping.get(channel_key)
            if channel_from_config:
                value.update(
                    {
                        "request_validators": channel_from_config.get("request_validators"),
                        "append_request_validators": channel_from_config.get("append_request_validators"),
                        "channel_classes": channel_from_config.get("channel_classes"),
                    }
                )

            channels.append((channel.path, value))

        return channels


def get_db_channel_manager() -> DBChannelManager:
    return DBChannelManager()
