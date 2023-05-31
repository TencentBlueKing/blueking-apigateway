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
import itertools
import logging
import operator

from django.core.management.base import BaseCommand

from esb.bkcore.models import ESBChannel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """update system and channel data to db"""

    def handle(self, *args, **options):
        """检查组件的 method+path 唯一性，同一 path 下，不能同时存在 method 为 '' 和其它请求方法"""
        channels = list(ESBChannel.objects.values("id", "method", "path"))
        channels = sorted(channels, key=operator.itemgetter("path"))
        for path, group in itertools.groupby(channels, key=operator.itemgetter("path")):
            method_to_channel = {channel["method"]: channel for channel in group}

            if len(method_to_channel) == 1:
                continue

            if "" in method_to_channel:
                empty_method_component_id = method_to_channel[""]["id"]
                logger.error(
                    f"component path [{path}] contains methods: {list(method_to_channel.keys())}, "
                    f"please split the component with the method '' [id={empty_method_component_id}] "
                    f"into two components with method GET and POST"
                )
