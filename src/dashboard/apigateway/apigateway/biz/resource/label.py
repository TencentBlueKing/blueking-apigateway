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
from typing import Dict, List

from apigateway.service.resource_snapshot import (
    get_resource_labels,
    get_resource_labels_by_gateway,
    get_resource_labels_by_ids,
)


class ResourceLabelHandler:
    @classmethod
    def get_labels_by_gateway(cls, gateway_id: int) -> Dict[int, List]:
        return get_resource_labels_by_gateway(gateway_id)

    @staticmethod
    def get_labels(resource_ids: List[int]) -> Dict[int, List]:
        return get_resource_labels(resource_ids)

    @staticmethod
    def get_labels_by_ids(label_ids: List[int]) -> Dict[int, List]:
        return get_resource_labels_by_ids(label_ids)
