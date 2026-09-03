#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from collections import defaultdict
from typing import DefaultDict, Dict, List, Set

from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Proxy, Release


class ProxyHandler:
    @staticmethod
    def get_resource_count_by_backend(gateway_id: int, backend_ids: List[int]) -> Dict[int, int]:
        """获取每个 backend 对应的资源个数"""
        if not backend_ids:
            return {}

        backend_id_set = set(backend_ids)
        resource_ids_by_backend: DefaultDict[int, Set[int]] = defaultdict(set)

        for backend_id, resource_id in Proxy.objects.filter(backend_id__in=backend_ids).values_list(
            "backend_id", "resource_id"
        ):
            resource_ids_by_backend[backend_id].add(resource_id)

        releases = Release.objects.filter(
            gateway_id=gateway_id,
            stage__status=StageStatusEnum.ACTIVE.value,
        ).select_related("resource_version")
        for release in releases:
            for resource_data in release.resource_version.data:
                backend_id = resource_data.get("proxy", {}).get("backend_id")
                resource_id = resource_data.get("id")
                if backend_id in backend_id_set and resource_id is not None:
                    resource_ids_by_backend[backend_id].add(resource_id)

        return {backend_id: len(resource_ids) for backend_id, resource_ids in resource_ids_by_backend.items()}
