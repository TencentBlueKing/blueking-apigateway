# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.common.fields import TimestampField


class AuditEventLogQueryInputSLZ(serializers.Serializer):
    time_start = TimestampField(allow_null=True, required=False, help_text="开始时间")
    time_end = TimestampField(allow_null=True, required=False, help_text="结束时间")

    keyword = serializers.CharField(allow_blank=True, required=False, help_text="关键字 (模糊)")

    op_object_type = serializers.ChoiceField(
        choices=OpObjectTypeEnum.get_choices(), allow_blank=True, required=False, help_text="操作对象"
    )
    op_type = serializers.ChoiceField(
        choices=OpTypeEnum.get_choices(), allow_blank=True, required=False, help_text="操作类型"
    )
    op_object = serializers.CharField(allow_blank=True, required=False, help_text="实例")
    username = serializers.CharField(allow_blank=True, required=False, help_text="操作人")

    class Meta:
        ref_name = "apigateway.apis.web.audit.serializers.AuditEventLogQueryInputSLZ"


class AuditEventLogOutputSLZ(serializers.ModelSerializer):
    class Meta:
        ref_name = "apigateway.apis.web.audit.serializers.AuditEventLogOutputSLZ"
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
            "data_before",
            "data_after",
            "comment",
        )
        read_only_fields = fields
        lookup_field = "id"

    def to_representation(self, value):
        data = super().to_representation(value)
        # translate comment
        if data["comment"]:
            data["comment"] = _(data["comment"])

        # the old version audit log has "api" as op_object_type, we need to convert it to "gateway"
        if data["op_object_type"] == "api":
            data["op_object_type"] = "gateway"

        if data["data_before"]:
            try:
                data["data_before"] = json.loads(data["data_before"])
            except Exception:  # pylint: disable=broad-except
                # do nothing here
                pass

        if data["data_after"]:
            try:
                data["data_after"] = json.loads(data["data_after"])
            except Exception:  # pylint: disable=broad-except
                # do nothing here
                pass

        return data
