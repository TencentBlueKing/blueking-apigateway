# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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


class ApplyStatusEnum(StructuredEnum):
    PARTIAL_APPROVED = EnumField("partial_approved", label=_("部分通过"))
    APPROVED = EnumField("approved", label=_("全部通过"))
    REJECTED = EnumField("rejected", label=_("全部驳回"))
    PENDING = EnumField("pending", label=_("待审批"))


# Restricted Enum subclassing
# https://docs.python.org/3/library/enum.html#restricted-subclassing-of-enumerations
class PermissionStatusEnum(StructuredEnum):
    UNLIMITED = EnumField("unlimited", label="无限制")
    APPROVED = EnumField("approved", label="已审批")
    REJECTED = EnumField("rejected", label="已拒绝")
    PENDING = EnumField("pending", label="申请中")
    NEED_APPLY = EnumField("need_apply", label="待申请")
    OWNED = EnumField("owned", label="已申请，且未过期")
    EXPIRED = EnumField("expired", label="已过期")


class PermissionActionEnum(StructuredEnum):
    APPLY = EnumField("apply")
    RENEW = EnumField("renew")


class PermissionLevelEnum(StructuredEnum):
    UNLIMITED = EnumField("unlimited", label=_("无限制"))
    NORMAL = EnumField("normal", label=_("普通"))
    SENSITIVE = EnumField("sensitive", label=_("敏感"))
    SPECIAL = EnumField("special", label=_("特殊"))


class PermissionApplyExpireDaysEnum(StructuredEnum):
    FOREVER = EnumField(0, label=_("永久"))
    SIX_MONTH = EnumField(180, label=_("6 个月"))
    TWELVE_MONTH = EnumField(360, label=_("12 个月"))


class GrantTypeEnum(StructuredEnum):
    # 初始化方式主动授权
    INITIALIZE = EnumField("initialize", label=_("主动授权"))
    # 申请审批方式授权
    APPLY = EnumField("apply", label=_("申请审批"))
    # 续期
    RENEW = EnumField("renew", label=_("续期"))
    # 自动续期
    AUTO_RENEW = EnumField("auto_renew", label=_("自动续期"))
    # 资源权限同步自按网关权限
    SYNC = EnumField("sync", label=_("按网关授权同步"))


class GrantDimensionEnum(StructuredEnum):
    """
    授权维度
    """

    API = EnumField("api", label=_("按网关"))
    RESOURCE = EnumField("resource", label=_("按资源"))


class FormattedGrantDimensionEnum(StructuredEnum):
    """
    格式化后的授权维度，放在 v2 api 中使用，仅对外，往 db 中写入还是得用 GrantDimensionEnum(存量数据)
    """

    GATEWAY = EnumField("gateway", label=_("网关"))
    RESOURCE = EnumField("resource", label=_("资源"))


# 默认的权限有效期天数
DEFAULT_PERMISSION_EXPIRE_DAYS = 180
# 可续期的过期天数，权限有效期小于此值，允许续期，否则，不允许
RENEWABLE_EXPIRE_DAYS = 360
