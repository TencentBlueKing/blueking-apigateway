# -*- coding: utf-8 -*-
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
from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.conf import settings
from django.utils.translation import gettext_lazy as _

TENANT_MODE_SINGLE_DEFAULT_TENANT_ID = "default"
TENANT_MODE_GLOBAL_DEFAULT_TENANT_ID = ""
TENANT_ID_OPERATION = "system"


class TenantModeEnum(StructuredEnum):
    """租户模式"""

    GLOBAL = EnumField("global", _("全租户"))
    SINGLE = EnumField("single", _("单租户"))


if settings.ENABLE_MULTI_TENANT_MODE:
    SELF_HOST_GATEWAY_DEFAULT_TENANT_MODE = TenantModeEnum.GLOBAL.value
    SELF_HOST_GATEWAY_DEFAULT_TENANT_ID = ""
else:
    SELF_HOST_GATEWAY_DEFAULT_TENANT_MODE = TenantModeEnum.SINGLE.value
    SELF_HOST_GATEWAY_DEFAULT_TENANT_ID = TENANT_MODE_SINGLE_DEFAULT_TENANT_ID
