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
from typing import Dict

from django.conf import settings

from .constants import (
    TENANT_ID_OPERATION,
    TENANT_MODE_SINGLE_DEFAULT_TENANT_ID,
)


def get_user_tenant_id(request) -> str:
    if settings.ENABLE_MULTI_TENANT_MODE:
        return request.user.tenant_id
    return TENANT_MODE_SINGLE_DEFAULT_TENANT_ID


def gen_operation_tenant_header() -> Dict[str, str]:
    return {"X-Bk-Tenant-Id": TENANT_ID_OPERATION}


def gen_tenant_header(tenant_id: str) -> Dict[str, str]:
    return {"X-Bk-Tenant-Id": tenant_id}
