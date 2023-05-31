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
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.audit.constants import OP_TYPE_CHOICES, OpObjectTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.common.fields import TimestampField


class AuditEventLogQuerySLZ(serializers.Serializer):
    time_start = TimestampField(allow_null=True, required=False)
    time_end = TimestampField(allow_null=True, required=False)
    op_object_type = serializers.ChoiceField(choices=OpObjectTypeEnum.choices(), allow_blank=True, required=False)
    op_type = serializers.ChoiceField(choices=OP_TYPE_CHOICES, allow_blank=True, required=False)
    username = serializers.CharField(allow_blank=True, required=False)


class AuditEventLogSLZ(serializers.ModelSerializer):
    class Meta:
        model = AuditEventLog
        fields = (
            "event_id",
            "system",
            "username",
            "op_time",
            "op_type",
            "op_status",
            "op_object_type",
            "op_object_id",
            "op_object",
            "comment",
        )
        read_only_fields = fields
        lookup_field = "id"

    def to_representation(self, value):
        data = super().to_representation(value)
        data["comment"] = self._translate_comment(data["comment"])
        return data

    def _translate_comment(self, comment) -> str:
        if comment:
            return _(comment)
        return ""
