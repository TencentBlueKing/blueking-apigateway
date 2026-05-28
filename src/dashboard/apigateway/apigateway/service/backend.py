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

from typing import Dict

from apigateway.core.models import Backend


def get_backend_id_to_instance(gateway_id: int) -> Dict[int, Backend]:
    """按 ID 查询网关下的后端服务实例，用于资源导出、资源版本展示等批量补全后端服务信息。

    调用方已有资源快照中的 backend_id，且需要避免循环查询 Backend 时使用。

    Args:
        gateway_id (int): 网关 ID，只查询该网关下的后端服务。

    Returns:
        Dict[int, Backend]: 键为后端服务 ID，值为对应 Backend 实例；没有数据时返回空字典。
    """
    return {backend.id: backend for backend in Backend.objects.filter(gateway_id=gateway_id)}
