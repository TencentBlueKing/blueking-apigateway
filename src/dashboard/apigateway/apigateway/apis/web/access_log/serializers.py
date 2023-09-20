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


class RequestLogQueryInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(required=True)
    query = serializers.CharField(label="查询条件", required=False, allow_blank=True)
    time_range = serializers.IntegerField(label="时间范围", required=False, min_value=0)
    time_start = serializers.IntegerField(label="起始时间", required=False, min_value=0)
    time_end = serializers.IntegerField(label="结束时间", required=False, min_value=0)
    offset = serializers.IntegerField(label="偏移量", required=False, min_value=0, default=0)
    limit = serializers.IntegerField(label="限制条数", required=False, min_value=1, default=10)

    def validate(self, data):
        if not (data.get("time_start") and data.get("time_end") or data.get("time_range")):
            raise serializers.ValidationError(_("参数 time_start+time_end, time_range 必须一组有效。"))
        return data


class TimeChartOutputSLZ(serializers.Serializer):
    series = serializers.ListField(child=serializers.IntegerField())
    timeline = serializers.ListField(child=serializers.IntegerField())


class RequestLogOutputSLZ(serializers.Serializer):
    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    timestamp = serializers.IntegerField(required=False, allow_null=True)
    stage = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    resource_id = serializers.IntegerField(required=False, allow_null=True)
    resource_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    app_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    client_ip = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    method = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    http_host = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    http_path = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    backend_method = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    backend_scheme = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    backend_host = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    backend_path = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    params = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    body = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    response_body = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.IntegerField(required=False, allow_null=True)
    headers = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    request_duration = serializers.IntegerField(required=False, allow_null=True)
    backend_duration = serializers.IntegerField(required=False, allow_null=True)
    code_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    response_desc = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class LogLinkOutputSLZ(serializers.Serializer):
    link = serializers.CharField(read_only=True)


class LogDetailQueryInputSLZ(serializers.Serializer):
    bk_nonce = serializers.IntegerField()
    bk_timestamp = serializers.IntegerField()
    bk_signature = serializers.CharField()
    shared_by = serializers.CharField()
