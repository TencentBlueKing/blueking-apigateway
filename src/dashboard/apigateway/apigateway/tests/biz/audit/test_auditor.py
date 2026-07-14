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

from django.test import TestCase

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.biz.audit import Auditor
from apigateway.core.backend_config import prepare_backend_config
from apigateway.core.constants import BackendKindEnum


def _stored_ai_config():
    return prepare_backend_config(
        BackendKindEnum.AI.value,
        {
            "timeout": 30000,
            "instances": [
                {
                    "name": "primary",
                    "provider": "openai",
                    "weight": 1,
                    "auth": {"header": {"Authorization": "Bearer secret"}},
                    "options": {"model": "gpt-4o"},
                }
            ],
        },
    )


class TestRecordAuditLog(TestCase):
    def test_record_audit_log(self):
        data = [
            {
                "username": "admin",
                "op_type": OpTypeEnum.CREATE,
                "gateway_id": "1",
                "instance_id": 123,
                "instance_name": "gateway: test",
                "data_before": '{"name": "test"}',
                "data_after": '{"name": "test"}',
                "comment": "test",
            }
        ]
        for test in data:
            Auditor.record_gateway_op_success(**test)
            logs = AuditEventLog.objects.filter(op_object_id="123")
            self.assertTrue(logs.exists())
            self.assertEqual(logs.count(), 1)

    def test_record_stage_backend_op_masks_model_data(self):
        stored_config = _stored_ai_config()

        Auditor.record_stage_backend_op_success(
            op_type=OpTypeEnum.MODIFY,
            username="admin",
            gateway_id=1,
            instance_id=123,
            instance_name="prod:openai-primary",
            backend_kind=BackendKindEnum.AI.value,
            data_before={"id": 123, "config": stored_config},
            data_after={"id": 123, "config": stored_config},
        )

        log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            op_object_id="123",
        )
        assert json.loads(log.data_before)["config"]["instances"][0]["auth"]["header"]["Authorization"] == ("Be****et")
        assert json.loads(log.data_after)["config"]["instances"][0]["auth"]["header"]["Authorization"] == ("Be****et")

    def test_record_stage_backend_op_masks_config_only_data(self):
        stored_config = _stored_ai_config()

        Auditor.record_stage_backend_op_success(
            op_type=OpTypeEnum.MODIFY,
            username="admin",
            gateway_id=1,
            instance_id=123,
            instance_name="prod:openai-primary",
            backend_kind=BackendKindEnum.AI.value,
            data_before=stored_config,
            data_after=stored_config,
        )

        log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            op_object_id="123",
        )
        assert json.loads(log.data_before)["instances"][0]["auth"]["header"]["Authorization"] == "Be****et"
        assert json.loads(log.data_after)["instances"][0]["auth"]["header"]["Authorization"] == "Be****et"

    def test_record_stage_backend_op_can_skip_unchanged_masked_data(self):
        stored_config = _stored_ai_config()

        Auditor.record_stage_backend_op_success(
            op_type=OpTypeEnum.MODIFY,
            username="admin",
            gateway_id=1,
            instance_id=123,
            instance_name="prod:openai-primary",
            backend_kind=BackendKindEnum.AI.value,
            data_before=stored_config,
            data_after=stored_config,
            skip_if_unchanged=True,
        )

        assert not AuditEventLog.objects.filter(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            op_object_id="123",
        ).exists()
