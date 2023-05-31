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
import datetime

import pytest
from ddf import G

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    ComponentSystem,
    ESBChannel,
)
from apigateway.apps.esb.permission import views
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


class TestAppPermissionApplyRecordViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, request_factory):
        self.factory = request_factory

    def test_list_pending(self, faker, unique_id):
        username = faker.user_name()
        G(AppPermissionApplyRecord, bk_app_code=unique_id, applied_by=username, status=ApplyStatusEnum.PENDING.value)
        G(AppPermissionApplyRecord, bk_app_code=unique_id, applied_by=username, status=ApplyStatusEnum.APPROVED.value)

        request = self.factory.get(
            "/",
            data={
                "bk_app_code": unique_id,
                "applied_by": "",
            },
        )

        view = views.AppPermissionApplyRecordViewSet.as_view({"get": "list_pending"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert len(result["data"]["results"]) == 1

    def test_list_handled(self, faker, unique_id):
        username = faker.user_name()
        G(AppPermissionApplyRecord, bk_app_code=unique_id, applied_by=username, status=ApplyStatusEnum.PENDING.value)
        G(AppPermissionApplyRecord, bk_app_code=unique_id, applied_by=username, status=ApplyStatusEnum.APPROVED.value)
        G(AppPermissionApplyRecord, bk_app_code=unique_id, applied_by=username, status=ApplyStatusEnum.REJECTED.value)

        request = self.factory.get(
            "/",
            data={
                "bk_app_code": unique_id,
                "applied_by": "",
            },
        )

        view = views.AppPermissionApplyRecordViewSet.as_view({"get": "list_handled"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert len(result["data"]["results"]) == 2

    def test_batch_handled(self, faker, unique_id):
        c = G(ESBChannel, board=unique_id)
        record = G(
            AppPermissionApplyRecord,
            board=unique_id,
            bk_app_code=unique_id,
            applied_by=faker.user_name(),
            status=ApplyStatusEnum.PENDING.value,
            _component_ids=f"{c.id}",
        )

        request = self.factory.post(
            "/",
            data={
                "ids": [record.id],
                "status": ApplyStatusEnum.APPROVED.value,
                "comment": "",
            },
        )

        view = views.AppPermissionApplyRecordViewSet.as_view({"post": "batch_handle"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert 1 == AppComponentPermission.objects.filter(bk_app_code=unique_id).count()


class TestAppComponentPermissionViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, request_factory):
        self.factory = request_factory

    def test_list(self, faker):
        system = G(ComponentSystem)
        c1 = G(ESBChannel, system=system)
        c2 = G(ESBChannel, system=system)
        p1 = G(AppComponentPermission, component_id=c1.id, expires=faker.past_datetime(tzinfo=datetime.timezone.utc))
        p2 = G(AppComponentPermission, component_id=c2.id, expires=faker.past_datetime(tzinfo=datetime.timezone.utc))

        request = self.factory.get(
            "/",
            data={
                "system_id": system.id,
            },
        )

        view = views.AppComponentPermissionViewSet.as_view({"get": "list"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert 2 == len(result["data"]["results"])

    def test_renew(self, faker):
        p1 = G(AppComponentPermission, expires=faker.past_datetime(tzinfo=datetime.timezone.utc))
        p2 = G(AppComponentPermission, expires=faker.past_datetime(tzinfo=datetime.timezone.utc))

        assert p1.expires_in < 0

        request = self.factory.post(
            "/",
            data={
                "ids": [p1.id],
            },
        )

        view = views.AppComponentPermissionViewSet.as_view({"post": "renew"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200

        p1 = AppComponentPermission.objects.get(id=p1.id)
        assert p1.expires_in > 0

    def test_destroy(self, faker, unique_id):
        p1 = G(AppComponentPermission, board=unique_id, expires=faker.past_datetime(tzinfo=datetime.timezone.utc))
        p2 = G(AppComponentPermission, board=unique_id, expires=faker.past_datetime(tzinfo=datetime.timezone.utc))

        request = self.factory.post(
            "/",
            data={
                "ids": [p1.id],
            },
        )

        view = views.AppComponentPermissionViewSet.as_view({"post": "destroy"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200

        assert 1 == AppComponentPermission.objects.filter(board=unique_id).count()
