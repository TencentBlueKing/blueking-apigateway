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
from typing import List

from apigateway.apps.label.models import APILabel
from apigateway.core.models import Gateway


class GatewayLabelHandler:
    @staticmethod
    def save_labels(gateway: Gateway, names: List[str], username: str = ""):
        exist_names = APILabel.objects.filter(gateway=gateway).values_list("name", flat=True)
        need_create_names = set(names) - set(exist_names)
        if not need_create_names:
            return

        labels = [
            APILabel(gateway=gateway, name=name, created_by=username, updated_by=username)
            for name in need_create_names
        ]
        APILabel.objects.bulk_create(labels, batch_size=100)

    @staticmethod
    def get_valid_ids(gateway_id: int, ids: List[int]) -> List[int]:
        return list(APILabel.objects.filter(gateway_id=gateway_id, id__in=ids).values_list("id", flat=True))
