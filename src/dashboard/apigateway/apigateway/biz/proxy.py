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
from typing import Dict, List

from django.db.models import Count

from apigateway.core.models import Proxy
from apigateway.schema.models import Schema


class ProxyHandler:
    @staticmethod
    def get_resource_id_to_snapshot(resource_ids: List[int]) -> Dict[int, Dict]:
        schemas = Schema.objects.filter_id_snapshot_map()
        return {
            proxy.resource_id: proxy.snapshot(as_dict=True, schemas=schemas)
            for proxy in Proxy.objects.filter(resource_id__in=resource_ids).prefetch_related("backend")
        }

    @staticmethod
    def get_resource_count_by_backend(backend_ids: List[int]) -> Dict[int, int]:
        """获取每个 backend 对应的资源个数"""
        qs = Proxy.objects.filter(backend_id__in=backend_ids).values("backend_id").annotate(count=Count("backend_id"))
        return {i["backend_id"]: i["count"] for i in qs}
