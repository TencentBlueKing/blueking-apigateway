# -*- coding: utf-8 -*-
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
import json
from unittest import mock

import pytest
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apis.web.permission import views
from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.permission import models
from apigateway.core.models import Resource
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, dummy_time, get_response_json
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestAppPermissionViewSet:
    def test_list(self, fake_gateway, request_view):
        fake_resource1 = G(Resource, name="name1", gateway=fake_gateway)
        fake_resource2 = G(Resource, name="name2", gateway=fake_gateway)

        G(
            models.AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="test",
            resource_id=fake_resource1.id,
            grant_type="apply",
        )
        G(
            models.AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="test-2",
            resource_id=fake_resource2.id,
            grant_type="apply",
        )

        G(
            models.AppGatewayPermission,
            gateway=fake_gateway,
            bk_app_code="test",
            handled_by="admin",
        )

        data = [
            {
                "params": {
                    "dimension": "resource",
                    "bk_app_code": "",
                    "grant_type": "apply",
                },
                "expected": {
                    "count": 2,
                    "status_code": 200,
                },
            },
            {
                "params": {
                    "resource_id": fake_resource1.id,
                },
                "expected": {
                    "count": 1,
                    "status_code": 200,
                },
            },
            {
                "params": {
                    "grant_dimension": "api",
                },
                "expected": {
                    "count": 1,
                    "status_code": 200,
                    "handled_by": "admin",
                },
            },
            {
                "params": {
                    "grant_dimension": "测试",
                },
                "expected": {
                    "count": 0,
                    "status_code": 400,
                },
            },
        ]

        for test in data:
            response = request_view(
                "GET",
                "permissions.app-permissions.list",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data=test["params"],
            )

            result = response.json()
            assert response.status_code == test["expected"]["status_code"], result
            if response.status_code == 200:
                assert result["data"]["count"] == test["expected"]["count"]
                if "handled_by" in test["expected"]:
                    assert result["data"]["results"][0]["handled_by"] == test["expected"]["handled_by"]


class TestAppPermissionRenewViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_renew(self):
        resource = G(Resource, gateway=self.gateway)

        resource_p1 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test",
            resource_id=resource.id,
            grant_type="initialize",
            handled_by="old-admin",
        )

        data = [
            {
                "params": {
                    "resource_dimension_ids": [resource_p1.id],
                    "gateway_dimension_ids": [],
                    "expire_days": 180,
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/gateways/{self.gateway.id}/permissions/app-permissions/renew/", data=test["params"]
            )

            view = views.AppPermissionRenewApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 201, result)

            resource_p1_obj = models.AppResourcePermission.objects.get(id=resource_p1.id)
            assert resource_p1_obj.grant_type == "initialize"
            assert resource_p1_obj.handled_by == "admin"

            audit_log = AuditEventLog.objects.get(op_object_id=str(resource_p1.id), comment="批量续期资源")
            assert audit_log.username == "admin"
            assert json.loads(audit_log.data_before)[0]["handled_by"] == "old-admin"
            assert json.loads(audit_log.data_after)[0]["handled_by"] == "admin"


class TestAppPermissionDeleteViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_destroy(self):
        resource = G(Resource, gateway=self.gateway)
        resource_perm = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-resource",
            resource_id=resource.id,
            grant_type="apply",
        )
        gateway_perm = G(
            models.AppGatewayPermission,
            gateway=self.gateway,
            bk_app_code="test-gateway",
        )
        resource_perm_name = str(resource_perm)
        gateway_perm_name = str(gateway_perm)

        request = self.factory.delete(
            f"/gateways/{self.gateway.id}/permissions/app-permissions/batch/",
            data={
                "resource_dimension_ids": [resource_perm.id],
                "gateway_dimension_ids": [gateway_perm.id],
            },
            format="json",
        )

        view = views.AppPermissionDeleteApi.as_view()
        with mock.patch.object(views.Auditor, "record_permission_op_success") as mocked_record:
            response = view(request, gateway_id=self.gateway.id)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            models.AppResourcePermission.objects.filter(gateway=self.gateway, id=resource_perm.id).exists()
        )
        self.assertFalse(models.AppGatewayPermission.objects.filter(gateway=self.gateway, id=gateway_perm.id).exists())
        self.assertEqual(mocked_record.call_count, 2)
        self.assertEqual(mocked_record.call_args_list[0].kwargs["instance_name"], resource_perm_name)
        self.assertEqual(mocked_record.call_args_list[1].kwargs["instance_name"], gateway_perm_name)

    def test_destroy_permission_not_found(self):
        request = self.factory.delete(
            f"/gateways/{self.gateway.id}/permissions/app-permissions/batch/",
            data={
                "resource_dimension_ids": [1],
                "gateway_dimension_ids": [2],
            },
            format="json",
        )

        view = views.AppPermissionDeleteApi.as_view()
        response = view(request, gateway_id=self.gateway.id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("权限不存在", str(response.data))


class TestAppResourcePermissionViewSet:
    def test_create(self, mocker, request_view, fake_resource):
        mocker.patch("apigateway.apps.permission.models.generate_expire_time", return_value=dummy_time.time)
        fake_gateway = fake_resource.gateway

        data = [
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": 180,
                    "resource_ids": [fake_resource.id],
                },
                "expected": {
                    "expires": dummy_time.time,
                    "permission_model": models.AppResourcePermission,
                },
            },
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": None,
                    "resource_ids": [fake_resource.id],
                },
                "expected": {
                    "expires": None,
                    "permission_model": models.AppResourcePermission,
                },
            },
        ]

        for test in data:
            response = request_view(
                "POST",
                "permissions.app-resource-permissions",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data=test["params"],
            )
            result = response.json()
            assert response.status_code == 201, result
            permission = test["expected"]["permission_model"].objects.get(
                gateway=fake_gateway,
                bk_app_code=test["params"]["bk_app_code"],
            )
            assert permission.handled_by == "admin"


class TestAppGatewayPermissionViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        mocker.patch("apigateway.apis.web.permission.serializers.BKAppCodeValidator.__call__")

    def test_create(self, mocker, request_view, fake_resource):
        mocker.patch("apigateway.apps.permission.models.generate_expire_time", return_value=dummy_time.time)
        fake_gateway = fake_resource.gateway

        data = [
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": 180,
                    "resource_ids": None,
                },
                "expected": {
                    "expires": dummy_time.time,
                    "permission_model": models.AppGatewayPermission,
                },
            },
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": None,
                    "resource_ids": None,
                },
                "expected": {
                    "expires": None,
                    "permission_model": models.AppGatewayPermission,
                },
            },
        ]

        for test in data:
            response = request_view(
                "POST",
                "permissions.app-gateway-permissions",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data=test["params"],
            )
            result = response.json()
            assert response.status_code == 201, result
            permission = test["expected"]["permission_model"].objects.get(
                gateway=fake_gateway,
                bk_app_code=test["params"]["bk_app_code"],
            )
            assert permission.handled_by == "admin"


class TestAppResourcePermissionBatchViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_renew(self):
        resource = G(Resource, gateway=self.gateway)

        perm_2 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test",
            resource_id=resource.id,
            grant_type="apply",
            handled_by="old-admin",
        )

        data = [
            {
                "params": {
                    "ids": [perm_2.id],
                    "expire_days": 180,
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/gateways/{self.gateway.id}/permissions/app-resource-permissions/renew/", data=test["params"]
            )

            view = views.AppResourcePermissionRenewApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 201, result)

            perm_record = models.AppResourcePermission.objects.filter(
                gateway=self.gateway,
                id=test["params"]["ids"][0],
            ).first()
            self.assertTrue(
                (180 + 180) * 24 * 3600 - 10
                < (perm_record.expires - now_datetime()).total_seconds()
                < (180 + 180) * 24 * 3600
            )
            self.assertEqual(perm_record.handled_by, "admin")

            audit_log = AuditEventLog.objects.get(op_object_id=str(perm_2.id), comment="资源权限续期")
            self.assertEqual(audit_log.username, "admin")
            self.assertEqual(json.loads(audit_log.data_before)[0]["handled_by"], "old-admin")
            self.assertEqual(json.loads(audit_log.data_after)[0]["handled_by"], "admin")

    def test_destroy(self):
        resource = G(Resource, gateway=self.gateway)

        perm_2 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test",
            resource_id=resource.id,
            grant_type="apply",
        )

        data = [
            {
                "ids": [perm_2.id],
            },
        ]

        for test in data:
            ids = ",".join([str(i) for i in test["ids"]])
            request = self.factory.delete(
                f"/gateways/{self.gateway.id}/permissions/app-resource-permissions/delete/?ids={ids}"
            )

            view = views.AppResourcePermissionDeleteApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            self.assertEqual(response.status_code, 204)

            permission_model = models.AppResourcePermission
            self.assertFalse(
                permission_model.objects.filter(
                    gateway=self.gateway,
                    id=test["ids"][0],
                ).exists()
            )


class TestAppGatewayPermissionBatchViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_renew(self):
        perm_1 = G(
            models.AppGatewayPermission,
            gateway=self.gateway,
            bk_app_code="test",
            handled_by="old-admin",
        )

        data = [
            {
                "params": {
                    "ids": [perm_1.id],
                    "expire_days": 180,
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/gateways/{self.gateway.id}/permissions/app-gateway-permissions/renew/", data=test["params"]
            )

            view = views.AppGatewayPermissionRenewApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 201, result)

            permission_model = models.AppGatewayPermission
            perm_record = permission_model.objects.filter(
                gateway=self.gateway,
                id=test["params"]["ids"][0],
            ).first()
            self.assertTrue(
                (180 + 180) * 24 * 3600 - 10
                < (perm_record.expires - now_datetime()).total_seconds()
                < (180 + 180) * 24 * 3600
            )
            self.assertEqual(perm_record.handled_by, "admin")

            audit_log = AuditEventLog.objects.get(op_object_id=str(perm_1.id), comment="网关权限续期")
            self.assertEqual(audit_log.username, "admin")
            self.assertEqual(json.loads(audit_log.data_before)[0]["handled_by"], "old-admin")
            self.assertEqual(json.loads(audit_log.data_after)[0]["handled_by"], "admin")

    def test_destroy(self):
        perm_1 = G(
            models.AppGatewayPermission,
            gateway=self.gateway,
            bk_app_code="test",
        )

        data = [
            {
                "ids": [perm_1.id],
                "expire_days": 180,
            },
        ]

        for test in data:
            ids = ",".join([str(i) for i in test["ids"]])
            request = self.factory.delete(
                f"/apis/{self.gateway.id}/permissions/app-gateway-permissions/delete/?ids={ids}"
            )

            view = views.AppGatewayPermissionDeleteApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            self.assertEqual(response.status_code, 204)

            permission_model = models.AppGatewayPermission
            self.assertFalse(
                permission_model.objects.filter(
                    gateway=self.gateway,
                    id=test["ids"][0],
                ).exists()
            )


class TestAppPermissionApplyViewSet:
    def test_list(self, request_factory, fake_gateway, settings):
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = (
            "https://example.com/#/ticket/ticketInfo?type=ticket&ticketId={ticket_id}"
        )

        G(
            models.AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test",
            itsm_ticket_id="102025092210362600001802",
        )

        data = [
            {
                "params": {
                    "bk_app_code": "test",
                    "applied_by": "",
                },
                "expected": {"count": 1},
            },
        ]

        for test in data:
            request = request_factory.get(
                f"/gateways/{fake_gateway.id}/permissions/app-permission-apply/",
                data=test["params"],
            )

            view = views.AppPermissionApplyListApi.as_view()
            response = view(request, gateway_id=fake_gateway.id)

            result = get_response_json(response)
            assert response.status_code == 200
            assert result["data"]["count"] == test["expected"]["count"]
            assert result["data"]["results"][0]["itsm_ticket_id"] == "102025092210362600001802"
            assert (
                result["data"]["results"][0]["itsm_ticket_url"]
                == "https://example.com/#/ticket/ticketInfo?type=ticket&ticketId=102025092210362600001802"
            )


class TestAppPermissionApplyBatchViewSet:
    def test_post(self, mocker, fake_gateway, request_factory):
        record_1 = G(
            models.AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test-api",
            status="approved",
            handled_by="admin",
        )
        record_2 = G(
            models.AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test-resource",
            status="rejected",
            handled_by="admin",
        )
        mocker.patch(
            "apigateway.biz.permission.GatewayPermissionDimensionManager.handle_permission_apply",
            return_value=record_1,
        )
        mocker.patch(
            "apigateway.biz.permission.ResourcePermissionDimensionManager.handle_permission_apply",
            return_value=record_2,
        )
        mocker.patch(
            "apigateway.apis.web.permission.views.send_mail_for_perm_handle",
            return_value=None,
        )

        apply_1 = G(
            models.AppPermissionApply,
            gateway=fake_gateway,
            grant_dimension="api",
        )

        apply_2 = G(
            models.AppPermissionApply,
            gateway=fake_gateway,
            _resource_ids="1,2,3",
            grant_dimension="resource",
        )

        data = [
            {
                "params": {
                    "ids": [apply_1.id],
                    "status": "approved",
                    "comment": "",
                },
            },
            {
                "params": {
                    "ids": [apply_2.id],
                    "status": "rejected",
                    "comment": "",
                    "part_resource_ids": {
                        f"{apply_2.id}": [2],
                    },
                },
            },
        ]

        for test in data:
            request = request_factory.post(
                f"/gateways/{fake_gateway.id}/permissions/app-permission-apply/approval/",
                data=test["params"],
            )

            view = views.AppPermissionApplyApprovalApi.as_view()
            response = view(request, gateway_id=fake_gateway.id)
            result = get_response_json(response)

            assert response.status_code == 201

        assert models.AppPermissionApply.objects.filter(gateway=fake_gateway).count() == 0
        assert AuditEventLog.objects.filter(comment="权限申请审批").count() == 2
        audit_log = AuditEventLog.objects.get(op_object_id=str(record_1.id), comment="权限申请审批")
        assert audit_log.username == "admin"
        assert json.loads(audit_log.data_after)["handled_by"] == "admin"
        assert json.loads(audit_log.data_after)["bk_app_code"] == "test-api"


class TestAppPermissionRecordViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_list(self):
        resource = G(Resource, gateway=self.gateway)
        G(
            models.AppPermissionRecord,
            gateway=self.gateway,
            bk_app_code="test",
            _resource_ids=f"{resource.id}",
            _handled_resource_ids=json.dumps(
                {
                    "approved": [resource.id],
                    "rejected": [],
                }
            ),
        )
        data = [
            {
                "params": {
                    "bk_app_code": "test",
                },
                "expected": {
                    "count": 1,
                },
            },
        ]

        for test in data:
            request = self.factory.get(
                f"/gateways/{self.gateway.id}/permissions/app-permission-records/", data=test["params"]
            )

            view = views.AppPermissionRecordListApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200, result)
            self.assertEqual(result["data"]["count"], test["expected"]["count"])

    def test_retrieve(self):
        resource = G(Resource, gateway=self.gateway)
        record = G(
            models.AppPermissionRecord,
            gateway=self.gateway,
            bk_app_code="test",
            _resource_ids=f"{resource.id}",
            _handled_resource_ids=json.dumps(
                {
                    "approved": [resource.id],
                    "rejected": [],
                }
            ),
        )

        request = self.factory.get(f"/gateways/{self.gateway.id}/permissions/app-permission-records/{record.id}/")

        view = views.AppPermissionRecordRetrieveApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=record.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 200, result)
