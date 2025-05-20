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

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _


class MCPServerStatusEnum(StructuredEnum):
    INACTIVE = EnumField(0, "已停用")
    ACTIVE = EnumField(1, "启用中")


class McpServerAppPermissionApplyExpireDaysEnum(StructuredEnum):
    FOREVER = EnumField(0, label=_("永久"))


class GrantTypeEnum(StructuredEnum):
    # 初始化方式主动授权
    INITIALIZE = EnumField("initialize", label=_("主动授权"))
    # 申请审批方式授权
    APPLY = EnumField("apply", label=_("申请审批"))


class McpServerAppPermissionApplyStatusEnum(StructuredEnum):
    APPROVED = EnumField("approved", label=_("通过"))
    REJECTED = EnumField("rejected", label=_("驳回"))
    PENDING = EnumField("pending", label=_("待审批"))
