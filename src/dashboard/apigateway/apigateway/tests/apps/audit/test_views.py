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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.audit.views import AuditEventLogViewSet
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json


class TestAuditEventLogViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_list(self):
        G(AuditEventLog, op_object_group=str(self.gateway.id), op_object_type="gateway", op_type="create")
        G(AuditEventLog, op_object_group=str(self.gateway.id), op_object_type="resource", op_type="modify")

        data = [
            {
                "op_object_type": "gateway",
                "expected": {
                    "count": 1,
                },
            },
            {
                "op_object_type": "resource",
                "expected": {
                    "count": 1,
                },
            },
            {
                "op_type": "create",
                "expected": {
                    "count": 1,
                },
            },
        ]

        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/audits/logs/", data=test)

            view = AuditEventLogViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"]["count"], test["expected"]["count"])
