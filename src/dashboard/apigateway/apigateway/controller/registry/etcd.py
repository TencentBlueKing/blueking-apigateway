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
from typing import ClassVar, Dict, Iterable, List, Optional, Type

import etcd3
from django.utils.encoding import force_str

from apigateway.controller.crds.base import KubernetesResource
from apigateway.controller.registry.base import Registry
from apigateway.utils.etcd import get_etcd_client
from apigateway.utils.yaml import yaml_dumps, yaml_loads

logger = logging.getLogger(__name__)


class EtcdRegistry(Registry):
    """Etcd 注册配置中心，数据实际存储在 etcd 中"""

    registry_type: ClassVar[str] = "etcd"

    def __init__(self, key_prefix: str, safe_mode: bool = True, etcd_client: etcd3.Etcd3Client = None):
        """
        :param safe_mode: 是否安全模式，如果为 True，从 etcd 读取的数据，反序列化失败时将抛出异常；否则，忽略这些数据
        """
        super().__init__(key_prefix)
        self.safe_mode = safe_mode
        self._etcd_client = etcd_client or get_etcd_client()

    def apply_resource(self, resource: KubernetesResource) -> bool:
        payload = yaml_dumps(resource.dict(by_alias=True))
        self._etcd_client.put(self._get_key(resource.kind, resource.metadata.name), payload)
        return True

    def sync_resources_by_key_prefix(self, resources: List[KubernetesResource]) -> List[KubernetesResource]:
        """按 key_prefix 同步资源，若 key_prefix 下的资源不在待同步资源列表中，将被删除；返回同步失败的资源列表"""
        sync_fail_resources = []
        remaining_keys = self._get_exist_keys_by_key_prefix()

        for resource in resources:
            key = self._get_key(resource.kind, resource.metadata.name)
            remaining_keys.pop(key, None)
            if not self.apply_resource(resource):
                sync_fail_resources.append(resource)

        for key in remaining_keys.keys():
            if not self._delete_by_key(key):
                logger.warning(
                    "failed to remove key [%s] from registry %s",
                    key,
                    self.registry_type,
                )

        return sync_fail_resources

    def _get_exist_keys_by_key_prefix(self) -> Dict[str, bool]:
        exist_keys: Dict[str, bool] = {}

        for _, kv_metadata in self._etcd_client.get_prefix(self.key_prefix, keys_only=True):
            exist_keys[force_str(kv_metadata.key)] = True

        return exist_keys

    def delete_resources_by_key_prefix(self):
        """删除 key_prefix 下的所有资源"""
        self._etcd_client.delete_prefix(self.key_prefix)

    def iter_by_type(self, resource_type: Type[KubernetesResource]) -> Iterable[KubernetesResource]:
        for payload, _ in self._etcd_client.get_prefix(self._get_kind_key_prefix(resource_type.kind)):
            cr = self._deserialize_cr(resource_type, payload)
            if cr:
                yield cr

    def _deserialize_cr(self, resource_type: Type[KubernetesResource], payload: str) -> Optional[KubernetesResource]:
        try:
            value = yaml_loads(payload)
            return resource_type(**value)
        except Exception as err:
            if not self.safe_mode:
                raise

            logger.warning("deserialize resource %s failed: %s", resource_type, err)

        return None

    def _delete_by_key(self, key: str) -> bool:
        return self._etcd_client.delete(key)
