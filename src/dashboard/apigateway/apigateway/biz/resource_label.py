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
from collections import defaultdict
from typing import Dict, List

from apigateway.apps.label.models import ResourceLabel
from apigateway.core.models import Resource


class ResourceLabelHandler:
    @classmethod
    def get_labels_by_gateway(cls, gateway_id: int) -> Dict[int, List]:
        resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
        return cls.get_labels(resource_ids)

    @staticmethod
    def get_labels(resource_ids: List[int]) -> Dict[int, List]:
        queryset = ResourceLabel.objects.filter(resource_id__in=resource_ids).values(
            "api_label_id", "api_label__name", "resource_id"
        )

        resource_labels = defaultdict(list)
        for label in queryset:
            resource_labels[label["resource_id"]].append(
                {
                    "id": label["api_label_id"],
                    "name": label["api_label__name"],
                }
            )

        return resource_labels
