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

from typing import List

from apigateway.apps.label.models import APILabel
from apigateway.core.models import Gateway


def save_gateway_labels(gateway: Gateway, names: List[str], username: str = ""):
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
