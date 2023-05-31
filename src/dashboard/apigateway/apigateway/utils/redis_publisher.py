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

from django.conf import settings

from apigateway.utils.redis_utils import get_redis_client
from apigateway.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class RedisPublisher(metaclass=Singleton):
    def __init__(self):
        self._channel_key = settings.APIGW_REVERSION_UPDATE_CHANNEL_KEY
        self._redis_client = get_redis_client("channel", getattr(settings, "CHANNEL_REDIS_CONFIG", None))

    def publish(self, message):
        if not self._redis_client:
            logger.warning(f"channel redis is none, publish to channel fail. message: {message}")
            return

        self._redis_client.publish(self._channel_key, message)
        logger.debug(f"publish to channel success. message: {message}")
