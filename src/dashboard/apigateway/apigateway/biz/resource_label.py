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

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.core.models import Gateway, Resource


class ResourceLabelHandler:
    @classmethod
    def get_labels_by_gateway(cls, gateway_id: int) -> Dict[int, List]:
        resource_ids = list(Resource.objects.filter(api_id=gateway_id).values_list("id", flat=True))
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

    @staticmethod
    def save_labels(gateway: Gateway, resource: Resource, label_ids: List[int]):
        """
        存储资源标签
        - 删除未指定的标签

        :param label_ids: 网关标签 ID，忽略不存在的标签
        """
        # 资源当前已有的标签
        remaining_resource_labels = {
            label.api_label_id: label.id for label in ResourceLabel.objects.filter(resource=resource)
        }

        add_resource_labels = []
        for gateway_label in APILabel.objects.filter(api=gateway, id__in=label_ids):
            if gateway_label.id in remaining_resource_labels:
                remaining_resource_labels.pop(gateway_label.id)
                continue

            add_resource_labels.append(ResourceLabel(resource=resource, api_label=gateway_label))

        if add_resource_labels:
            # resource label 最多 10 个，不需要指定 batch_size
            ResourceLabel.objects.bulk_create(add_resource_labels)

        if remaining_resource_labels:
            ResourceLabel.objects.filter(id__in=remaining_resource_labels.values()).delete()
