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
from apigateway.apps.audit.serializers import AuditEventLogSLZ
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import dummy_time


class TestAuditEventLogSLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)

    def test_to_representation(self):
        data = [
            # event_id with '10a7324e4cd341edbfaace38472915d2'
            {
                "instance": G(
                    AuditEventLog,
                    event_id="10a7324e4cd341edbfaace38472915d2",
                    system="apigateway-dashboard",
                    username="admin",
                    op_time=dummy_time.time,
                    op_type="create",
                    op_status="success",
                    op_object_type="gateway",
                    op_object_id="123",
                    op_object="gateway: 123",
                    comment="comment",
                ),
                "expected": {
                    "event_id": "10a7324e4cd341edbfaace38472915d2",
                    "system": "apigateway-dashboard",
                    "username": "admin",
                    "op_time": dummy_time.str,
                    "op_type": "create",
                    "op_status": "success",
                    "op_object_type": "gateway",
                    "op_object_id": "123",
                    "op_object": "gateway: 123",
                    "comment": "comment",
                },
            },
            # event_id with '10a7324e-4cd3-41ed-bfaa-ce38472915d2'
            {
                "instance": G(
                    AuditEventLog,
                    event_id="10a7324e-4cd3-41ed-bfaa-ce38472915d2",
                    system="apigateway-dashboard",
                    username="admin",
                    op_time=dummy_time.time,
                    op_type="create",
                    op_status="success",
                    op_object_type="gateway",
                    op_object_id="123",
                    op_object="gateway: 123",
                    comment="comment",
                ),
                "expected": {
                    "event_id": "10a7324e-4cd3-41ed-bfaa-ce38472915d2",
                    "system": "apigateway-dashboard",
                    "username": "admin",
                    "op_time": dummy_time.str,
                    "op_type": "create",
                    "op_status": "success",
                    "op_object_type": "gateway",
                    "op_object_id": "123",
                    "op_object": "gateway: 123",
                    "comment": "comment",
                },
            },
        ]
        for test in data:
            slz = AuditEventLogSLZ(instance=test["instance"])
            self.assertEqual(slz.data, test["expected"])
