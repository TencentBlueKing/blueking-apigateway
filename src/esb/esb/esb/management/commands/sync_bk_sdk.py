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

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.sdk_management.utils import SDKGenerator
from esb.management.utils import conf_tools

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """生成最新SDK"""

    def get_target_dir(self):
        return getattr(settings, "SDK_TARGET_DIR", "/tmp/open_paas_esb_sdk/")

    def handle(self, *args, **options):
        conf_client = conf_tools.ConfClient()
        sdk_channels = conf_client.default_channels
        for system_name, system_channels in list(conf_client.confapis_channels.items()):
            sdk_channels.setdefault(system_name, [])
            sdk_channels[system_name].extend(system_channels)

        sdk_generator = SDKGenerator(
            channels=sdk_channels,
            target_dir=self.get_target_dir(),
        )
        sdk_generator.generate_sdk_files()
        logger.info("generate open_pass_esb sdk files to %s" % self.get_target_dir())
