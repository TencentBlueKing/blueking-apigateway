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
from __future__ import annotations

from typing import TYPE_CHECKING

from apigw_manager.apigw.helper import ContextManager
from django.utils import timezone

if TYPE_CHECKING:
    from datetime import datetime

INITIAL_SYNC_COMPLETED_AT_KEY = "gateway_rbac_initial_sync_completed_at"


class GatewayIAMSyncContext(ContextManager):
    """Persist IAM initialization metadata in the shared manager context."""

    scope = "iam_v4"

    def is_initial_sync_completed(self) -> bool:
        return bool(self.get_value(INITIAL_SYNC_COMPLETED_AT_KEY))

    def mark_initial_sync_completed(self, completed_at: datetime | None = None) -> None:
        self.set_value(INITIAL_SYNC_COMPLETED_AT_KEY, (completed_at or timezone.now()).isoformat())
