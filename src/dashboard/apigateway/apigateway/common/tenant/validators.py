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

from django.utils.translation import gettext as _

from apigateway.common.error_codes import error_codes

from .constants import (
    TenantModeEnum,
)


def check_user_can_access_gateway(gateway_tenant_mode: str, gateway_tenant_id: str, user_tenant_id: str) -> None:
    """用户是否能访问网关

    Args:
        gateway_tenant_mode (str): 网关租户模式
        gateway_tenant_id (str): 网关租户 id
        user_tenant_id (str): user tenant id

    """
    # 全租户网关，所有人都能访问
    if gateway_tenant_mode == TenantModeEnum.GLOBAL.value:
        return

    if gateway_tenant_id != user_tenant_id:
        raise error_codes.NO_PERMISSION.format(_("您没有权限访问该网关，该网关不属于你所在的租户"))
