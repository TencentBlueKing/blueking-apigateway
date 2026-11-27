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

from blue_krill.data_types.enum import EnumField, StructuredEnum


# PaaS 部署、下架操作的状态
class PaaSDeployStatusEnum(StructuredEnum):
    SUCCESSFUL = EnumField("successful", "successful")  # 成功
    FAILED = EnumField("failed", "failed")  # 失败
    PENDING = EnumField("pending", "pending")  # 执行中
    INTERRUPTED = EnumField("interrupted", "interrupted")  # 已中断


# 操作结束后的状态，进入后不再变化
PAAS_DEPLOY_FINISHED_STATUSES = [
    PaaSDeployStatusEnum.SUCCESSFUL.value,
    PaaSDeployStatusEnum.FAILED.value,
    PaaSDeployStatusEnum.INTERRUPTED.value,
]
