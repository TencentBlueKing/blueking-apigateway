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
import logging

from django.dispatch import Signal, receiver

from apigateway.apps.audit.models import AuditEventLog

logger = logging.getLogger(__name__)


_record_audit_log_signal = Signal(
    providing_args=[
        "event_id",
        "system",
        "username",
        "op_type",
        "op_status",
        "op_object_group",
        "op_object_type",
        "op_object_id",
        "op_object",
        "data_before",
        "data_after",
        "comment",
    ]
)


@receiver(_record_audit_log_signal, dispatch_uid="record_audit_log")
def _record_audit_log(sender, **kwargs):
    kwargs.pop("signal", None)

    try:
        AuditEventLog.objects.create(**kwargs)
    except Exception:
        logger.exception("log audit event log fail, kwargs=%s", kwargs)
