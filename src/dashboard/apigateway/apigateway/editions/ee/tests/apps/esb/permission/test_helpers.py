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
import pytest
from ddf import G

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    AppPermissionApplyStatus,
    ComponentSystem,
    ESBChannel,
)
from apigateway.apps.esb.permission.helpers import PermissionManager
from apigateway.apps.permission.constants import ApplyStatusEnum

pytestmark = pytest.mark.django_db


class TestPermissionManager:
    def test_handle_permission_apply(self, faker):
        system = G(ComponentSystem)
        c1 = G(ESBChannel, system=system)
        c2 = G(ESBChannel, system=system)

        record = G(AppPermissionApplyRecord)
        record.component_ids = [c1.id, c2.id]
        record.save()

        G(AppPermissionApplyStatus, record=record, system=system, component=c1)
        G(AppPermissionApplyStatus, record=record, system=system, component=c2)

        manager = PermissionManager()
        manager.handle_permission_apply(
            record,
            ApplyStatusEnum.PARTIAL_APPROVED.value,
            comment="comment",
            handled_by=faker.user_name(),
            part_component_ids=[c1.id],
        )

        record = AppPermissionApplyRecord.objects.get(id=record.id)
        assert record.status == ApplyStatusEnum.PARTIAL_APPROVED.value
        assert record.handled_component_ids == {
            ApplyStatusEnum.APPROVED.value: [c1.id],
            ApplyStatusEnum.REJECTED.value: [c2.id],
        }

        assert 1 == AppPermissionApplyStatus.objects.filter(component_id__in=[c1.id, c2.id]).count()
        assert (
            1
            == AppComponentPermission.objects.filter(
                board=record.board,
                bk_app_code=record.bk_app_code,
                component_id__in=[c1.id, c2.id],
            ).count()
        )

    def test_handle_apply_status(self):
        system = G(ComponentSystem)
        c1 = G(ESBChannel, system=system)
        c2 = G(ESBChannel, system=system)
        record = G(AppPermissionApplyRecord)
        G(AppPermissionApplyStatus, record=record, system=system, component=c1)
        G(AppPermissionApplyStatus, record=record, system=system, component=c2)

        manager = PermissionManager()
        manager._handle_apply_status(record, rejected_component_ids=[c2.id])

        assert 1 == AppPermissionApplyStatus.objects.filter(component_id__in=[c1.id, c2.id]).count()

        apply_status = AppPermissionApplyStatus.objects.get(component_id=c2.id)
        assert apply_status.record is None
        assert apply_status.status == ApplyStatusEnum.REJECTED.value

    @pytest.mark.parametrize(
        "status, component_ids, part_component_ids, expected",
        [
            (
                ApplyStatusEnum.APPROVED.value,
                [1, 2, 3],
                None,
                ([1, 2, 3], []),
            ),
            (
                ApplyStatusEnum.REJECTED.value,
                [1, 2, 3],
                None,
                ([], [1, 2, 3]),
            ),
            (
                ApplyStatusEnum.PARTIAL_APPROVED.value,
                [1, 2, 3],
                [2],
                ([2], [1, 3]),
            ),
        ],
    )
    def test_split_component_ids(self, status, component_ids, part_component_ids, expected):
        manager = PermissionManager()
        result = manager._split_component_ids(status, component_ids, part_component_ids)
        assert result == expected
