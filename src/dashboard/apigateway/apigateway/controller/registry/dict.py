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
from copy import deepcopy
from typing import ClassVar, Dict, Iterable, List, Type

from apigateway.controller.crds.base import KubernetesResource
from apigateway.controller.registry.base import Registry

logger = logging.getLogger(__name__)


class DictRegistry(Registry):
    """内存配置注册中心"""

    registry_type: ClassVar[str] = "dict"

    def __init__(self, key_prefix: str = ""):
        super().__init__(key_prefix)
        self._registry_dict: Dict[str, KubernetesResource] = {}

    def apply_resource(self, resource: KubernetesResource) -> bool:
        self._registry_dict[self._get_key(resource.kind, resource.metadata.name)] = deepcopy(resource)
        return True

    def sync_resources_by_key_prefix(self, resources: Iterable[KubernetesResource]) -> List[KubernetesResource]:
        self.delete_resources_by_key_prefix()

        for resource in resources:
            self.apply_resource(resource)

        return []

    def delete_resources_by_key_prefix(self):
        self._registry_dict.clear()

    def iter_by_type(self, resource_type: Type[KubernetesResource]) -> Iterable[KubernetesResource]:
        kind_key_prefix = self._get_kind_key_prefix(resource_type.kind)
        for key, resource in self._registry_dict.items():
            if key.startswith(kind_key_prefix):
                yield deepcopy(resource)

    def _get_exist_keys_by_key_prefix(self) -> Dict[str, bool]:
        """用于单元测试"""
        return {k: True for k in self._registry_dict.keys()}
