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
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class KeyPrefixHandler:
    api_version: str = "v1beta1"
    prefix: str = settings.BK_GATEWAY_ETCD_NAMESPACE_PREFIX

    def get_release_key_prefix(self, micro_gateway_name: str, gateway_name: str, stage_name: str) -> str:
        """利用微网关名称、网关名称、环境名称，构造发布的键前缀；在 etcd 中，一次发布的所有数据，都会在此前缀下"""
        return f"{self.prefix}/{micro_gateway_name}/{gateway_name}/{stage_name}/{self.api_version}/"
