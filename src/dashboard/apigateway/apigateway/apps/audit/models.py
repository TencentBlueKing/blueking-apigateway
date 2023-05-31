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
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.audit.constants import OP_STATUS_CHOICES, OP_TYPE_CHOICES
from apigateway.apps.audit.managers import AuditEventLogManager


class AuditEventLog(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    system = models.CharField(max_length=64, blank=False, null=False)
    username = models.CharField(max_length=64, blank=False, null=False)

    op_time = models.DateTimeField(auto_now_add=True, db_index=True)
    op_type = models.CharField(max_length=32, choices=OP_TYPE_CHOICES, blank=False, null=False, db_index=True)
    op_status = models.CharField(max_length=32, choices=OP_STATUS_CHOICES, blank=False, null=False)

    op_object_group = models.CharField(max_length=64, db_index=True, blank=False, null=False)
    op_object_type = models.CharField(max_length=32, blank=False, null=False, db_index=True)
    op_object_id = models.CharField(max_length=64, blank=True, null=True)
    op_object = models.CharField(max_length=512, blank=True, null=True)

    data_before = models.TextField(null=True, blank=True)
    data_after = models.TextField(null=True, blank=True)

    comment = models.TextField(null=True, blank=True)

    objects = AuditEventLogManager()

    def __str__(self):
        return f"<AuditEventLog: {self.event_id}>"

    class Meta:
        verbose_name = _("操作审计日志")
        verbose_name_plural = _("操作审计日志")
        db_table = "audit_event_log"
