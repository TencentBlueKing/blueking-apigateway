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
from datetime import timedelta

from apigateway.apps.rbac.constants import GATEWAY_MEMBER_EXPIRE_DAYS

SYSTEM_NAME = "蓝鲸 API 网关"
SYSTEM_DESCRIPTION = "蓝鲸 API 网关 RBAC 权限管理"
BK_IAM_V4_SYSTEM_ID = "bk_apigateway"

ALLOW_CACHE_TTL = 60
DEFAULT_MEMBER_EXPIRY = timedelta(days=GATEWAY_MEMBER_EXPIRE_DAYS)
EXPIRY_TOLERANCE = timedelta(minutes=1)

REASON_MISSING_GRANT = "missing"
REASON_ROLE_MISMATCH_GRANT = "role-mismatch"
REASON_EXPIRY_REFRESH_GRANT = "expiry-refresh"
REASON_ROLE_MISMATCH_REVOKE = "role-mismatch"
REASON_EXTRA_REVOKE = "extra"
