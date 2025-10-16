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
from abc import ABC, abstractmethod
from typing import ClassVar, Iterable, List, Type

from apigateway.controller.models.base import ApisixModel

logger = logging.getLogger(__name__)


class Registry(ABC):
    """配置注册中心，本质上是一个 KV 结构的存储，可以同时存储多种类型的资源，并可以进行迭代，修改和查询等操作"""

    registry_type: ClassVar[str]

    def __init__(self, key_prefix: str):
        """
        :param key_prefix: 配置注册中心当前管理数据 key 的前缀
        """
        # key_prefix 应以 / 结尾，防止筛选数据出现错误；如 key_prefix 为 /foo 时，不应该过滤出 /foo2 的数据
        self.key_prefix = key_prefix if key_prefix.endswith("/") else f"{key_prefix}/"

    @abstractmethod
    def apply_resource(self, resource: ApisixModel) -> bool:
        """写入资源"""
        raise NotImplementedError()

    @abstractmethod
    def sync_resources_by_key_prefix(self, resources: List[ApisixModel]) -> List[ApisixModel]:
        """按 key_prefix 同步资源，若 key_prefix 下的资源不在待同步资源列表中，将被删除

        :return: 返回同步失败的资源列表
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_resources_by_key_prefix(self):
        """删除 key_prefix 下的所有资源"""
        raise NotImplementedError()

    @abstractmethod
    def iter_by_type(self, resource_type: Type[ApisixModel]) -> Iterable[ApisixModel]:
        """获取 key_prefix 下，指定类型的资源"""
        raise NotImplementedError()

    def _get_kind_key_prefix(self, kind: str) -> str:
        """获取到 kind 的 key 前缀

        :param kind: ApisixModel 的 kind
        """
        return f"{self.key_prefix}{kind}/"

    def _get_key(self, kind: str, id: str) -> str:
        """获取资源在配置中心中完整的 key

        :param kind: ApisixModel 的 kind
        :param id: ApisixModel 的 id
        """
        return f"{self._get_kind_key_prefix(kind)}{id}"
