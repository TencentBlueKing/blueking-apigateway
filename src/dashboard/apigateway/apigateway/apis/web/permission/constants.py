# -*- coding: utf-8 -*-
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

from apigateway.common.constants import ChoiceEnum


class GrantTypeEnum(ChoiceEnum):
    # 初始化方式主动授权
    INITIALIZE = "initialize"
    # 申请审批方式授权
    APPLY = "apply"
    # 续期
    RENEW = "renew"
    # 自动续期
    AUTO_RENEW = "auto_renew"
    # 资源权限同步自按网关权限
    SYNC = "sync"


class PermissionApplyExpireDaysEnum(StructuredEnum):
    FOREVER = EnumField(0, label=_("永久"))
    SIX_MONTH = EnumField(180, label=_("6个月"))
    TWELVE_MONTH = EnumField(360, label=_("12个月"))


class GrantDimensionEnum(StructuredEnum):
    """
    授权维度
    """

    API = EnumField("api", label=_("按网关"))
    RESOURCE = EnumField("resource", label=_("按资源"))


class ApplyStatusEnum(StructuredEnum):
    PARTIAL_APPROVED = EnumField("partial_approved", label=_("部分通过"))
    APPROVED = EnumField("approved", label=_("全部通过"))
    REJECTED = EnumField("rejected", label=_("全部驳回"))
    PENDING = EnumField("pending", label=_("待审批"))


# 可续期的过期天数，权限有效期小于此值，允许续期，否则，不允许
RENEWABLE_EXPIRE_DAYS = 30
