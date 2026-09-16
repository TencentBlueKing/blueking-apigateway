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
from datetime import UTC, datetime

import pytest
from apigw_manager.apigw.models import Context as ManagerContext

from apigateway.apps.rbac.iam_context import (
    INITIAL_SYNC_COMPLETED_AT_KEY,
    GatewayIAMSyncContext,
)

pytestmark = pytest.mark.django_db


def test_initial_sync_is_incomplete_without_context():
    assert not GatewayIAMSyncContext().is_initial_sync_completed()


def test_mark_initial_sync_completed_persists_timestamp():
    completed_at = datetime(2026, 9, 11, 9, 30, tzinfo=UTC)
    context = GatewayIAMSyncContext()

    context.mark_initial_sync_completed(completed_at)

    assert context.is_initial_sync_completed()
    assert (
        ManagerContext.objects.get(
            scope=GatewayIAMSyncContext.scope,
            key=INITIAL_SYNC_COMPLETED_AT_KEY,
        ).value
        == completed_at.isoformat()
    )
