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

"""Resource label lookup and idempotent gateway label creation."""

from collections import defaultdict
from typing import Dict, List

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.core.models import Gateway, Resource


def get_resource_id_to_labels(resource_ids: List[int]) -> Dict[int, List]:
    """批量查询资源绑定的标签，用于为资源列表、详情和资源版本快照补全标签信息。

    调用方已经有资源 ID 列表，需要按资源 ID 聚合标签 ID 和名称时使用。

    Args:
        resource_ids (List[int]): 资源 ID 列表。

    Returns:
        Dict[int, List]: 键为资源 ID，值为标签列表；每个标签包含 id 和 name。
    """
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


def get_gateway_resource_id_to_labels(gateway_id: int) -> Dict[int, List]:
    """查询网关下所有资源绑定的标签，用于创建资源版本或导出资源时获取资源标签映射。

    调用方只有网关 ID，需要一次性获取该网关所有资源的标签时使用。

    Args:
        gateway_id (int): 网关 ID。

    Returns:
        Dict[int, List]: 键为资源 ID，值为标签列表；没有资源或标签时返回空字典。
    """
    resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
    return get_resource_id_to_labels(resource_ids)


def get_resource_id_to_labels_by_label_ids(label_ids: List[int]) -> Dict[int, List]:
    """按标签 ID 查询资源标签绑定关系，用于根据标签筛选或补全资源。

    调用方已经有标签 ID 列表，需要按资源 ID 聚合标签信息时使用。

    Args:
        label_ids (List[int]): 标签 ID 列表。

    Returns:
        Dict[int, List]: 键为资源 ID，值为命中的标签列表。
    """
    queryset = ResourceLabel.objects.filter(api_label_id__in=label_ids).values(
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


def ensure_gateway_labels(gateway: Gateway, names: List[str], username: str = ""):
    """按名称补齐网关标签，用于导入或同步资源时确保资源引用的标签名称已存在。

    调用方只关心缺失标签的创建，不需要更新已有标签或返回标签对象时使用。

    Args:
        gateway (Gateway): 标签所属网关。
        names (List[str]): 需要确保存在的标签名称列表。
        username (str): 创建缺失标签时写入 created_by / updated_by 的用户名。

    Returns:
        None: 函数只负责创建缺失标签，不返回创建结果。
    """
    exist_names = APILabel.objects.filter(gateway=gateway).values_list("name", flat=True)
    need_create_names = set(names) - set(exist_names)
    if not need_create_names:
        return

    APILabel.objects.bulk_create(
        [APILabel(gateway=gateway, name=name, created_by=username, updated_by=username) for name in need_create_names],
        batch_size=100,
    )
