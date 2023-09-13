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
import math

import pytest
from ddf import G

from apigateway.apis.open.esb.permission import views
from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord, ComponentSystem, ESBChannel
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


class TestComponentViewSet:
    def test_list(self, mocker, request_factory):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BoardConfigManager.get_optional_display_label",
            return_value="my-test",
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.views.ComponentPermissionBuilder.build",
            return_value=[
                {
                    "id": 1,
                    "board": "test",
                    "name": "test",
                    "system_name": "test",
                    "description": "test",
                    "description_en": "test_en",
                    "expires_in": math.inf,
                    "permission_level": "normal",
                    "permission_status": "owned",
                    "doc_link": "",
                    "tag": "",
                }
            ],
        )

        params = {
            "target_app_code": "test",
        }

        request = request_factory.get("/", data=params)

        view = views.ComponentViewSet.as_view({"get": "list"})
        response = view(request, system_id=1)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"] == [
            {
                "id": 1,
                "name": "test",
                "system_name": "test",
                "description": "test",
                "description_en": "test_en",
                "expires_in": None,
                "permission_level": "normal",
                "permission_status": "owned",
                "permission_action": "",
                "doc_link": "",
                "tag": "my-test",
            }
        ]


class TestAppPermissionApplyV1APIView:
    def test_apply(self, mocker, request_factory, unique_id):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.views.send_mail_for_perm_apply.apply_async",
            return_value=None,
        )

        system = G(ComponentSystem)
        channel = G(ESBChannel, system=system)

        params = {
            "target_app_code": unique_id,
            "component_ids": [channel.id],
            "reason": "",
            "expire_days": 180,
        }

        request = request_factory.post("", data=params)

        view = views.AppPermissionApplyV1APIView.as_view({"post": "apply"})
        response = view(request, system_id=system.id)

        result = get_response_json(response)
        assert result["code"] == 0, result
        assert AppPermissionApplyRecord.objects.filter(bk_app_code=unique_id).exists()


class TestAppPermissionViewSet:
    def test_list(self, mocker, request_factory):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.views.AppComponentPermission.objects.filter_component_ids",
            return_value=[1],
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.views.ComponentPermissionBuilder.build",
            return_value=[
                {
                    "board": "test",
                    "id": 1,
                    "name": "test",
                    "system_name": "test",
                    "description": "desc",
                    "description_en": "desc_en",
                    "expires_in": 10,
                    "permission_level": "nomal",
                    "permission_status": "owned",
                    "permission_action": "",
                    "doc_link": "",
                },
            ],
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BoardConfigManager.get_optional_display_label",
            return_value="my-test",
        )

        params = {
            "target_app_code": "test",
        }

        request = request_factory.get("/", data=params)

        view = views.AppPermissionViewSet.as_view({"get": "list"})
        response = view(request)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"] == [
            {
                "id": 1,
                "name": "test",
                "system_name": "test",
                "description": "desc",
                "description_en": "desc_en",
                "expires_in": 10,
                "permission_level": "nomal",
                "permission_status": "owned",
                "permission_action": "renew",
                "doc_link": "",
                "tag": "my-test",
            }
        ]


class TestAppPermissionApplyRecordViewSet:
    def test_list(self, mocker, request_factory, unique_id):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BoardConfigManager.get_optional_display_label",
            return_value="my-test",
        )
        params = {
            "target_app_code": unique_id,
        }

        system = G(ComponentSystem, name=unique_id)

        record = AppPermissionApplyRecord.objects.create_record(
            board="test",
            bk_app_code=unique_id,
            applied_by="admin",
            system=system,
            component_ids=[1, 2, 3],
            status="pending",
            reason="test",
            expire_days=180,
        )

        request = request_factory.get("/backend/api/v1/", data=params)

        view = views.AppPermissionApplyRecordViewSet.as_view({"get": "list"})
        response = view(request)

        result = get_response_json(response)
        assert result["data"]["count"] == 1
        assert result["data"]["has_next"] is False
        assert result["data"]["has_previous"] is False
        assert len(result["data"]["results"]) == 1

    def test_retrieve(self, mocker, request_factory, unique_id):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        params = {
            "target_app_code": unique_id,
        }

        system = G(ComponentSystem, name=unique_id)
        c = G(
            ESBChannel,
            system=system,
            name="test",
            description="desc",
            is_active=True,
        )

        record = AppPermissionApplyRecord.objects.create_record(
            board="test",
            bk_app_code=unique_id,
            applied_by="admin",
            system=system,
            component_ids=[c.id],
            status="pending",
            reason="test",
            expire_days=180,
        )

        request = request_factory.get("/", data=params)

        view = views.AppPermissionApplyRecordViewSet.as_view({"get": "retrieve"})
        response = view(request, record.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"]["id"] == record.id
        assert result["data"]["bk_app_code"] == unique_id
        assert result["data"]["components"] == [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "description_en": c.description_en,
                "apply_status": "pending",
            }
        ]
