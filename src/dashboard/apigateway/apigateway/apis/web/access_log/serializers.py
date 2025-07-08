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
from typing import List, Tuple

from django.utils.translation import gettext as _
from rest_framework import serializers


class RequestLogQueryInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(required=True, help_text="环境 ID")
    resource_id = serializers.IntegerField(allow_null=True, required=False, help_text="资源 ID")
    query = serializers.CharField(label="查询条件", required=False, allow_blank=True, help_text="查询条件")
    # ?include=xxx:yyy&include=aaa:bbb
    include = serializers.ListField(child=serializers.CharField(), required=False, help_text="包含条件")
    # ?exclude=xxx:yyy&exclude=aaa:bbb
    exclude = serializers.ListField(child=serializers.CharField(), required=False, help_text="排除条件")
    time_range = serializers.IntegerField(label="时间范围", required=False, min_value=0, help_text="时间范围")
    time_start = serializers.IntegerField(label="起始时间", required=False, min_value=0, help_text="起始时间")
    time_end = serializers.IntegerField(label="结束时间", required=False, min_value=0, help_text="结束时间")
    offset = serializers.IntegerField(label="偏移量", required=False, min_value=0, default=0, help_text="偏移量")
    limit = serializers.IntegerField(label="限制条数", required=False, min_value=1, default=10, help_text="限制条数")

    class Meta:
        ref_name = "apigateway.apis.web.access_log.serializers.RequestLogQueryInputSLZ"

    def validate(self, data):
        if not (data.get("time_start") and data.get("time_end") or data.get("time_range")):
            raise serializers.ValidationError(_("参数 time_start+time_end, time_range 必须一组有效。"))
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        include_conditions: List[Tuple[str, str]] = []
        if data.get("include"):
            # aaa:bbb => {aaa: bbb}, aaa:bbb:ccc => {aaa: bbb:ccc}
            for expr in data["include"]:
                if ":" not in expr:
                    continue
                k, v = expr.split(":", 1)
                include_conditions.append((k, v))

        if include_conditions:
            data["include_conditions"] = include_conditions

        exclude_conditions: List[Tuple[str, str]] = []
        if data.get("exclude"):
            for expr in data["exclude"]:
                if ":" not in expr:
                    continue
                k, v = expr.split(":", 1)
                exclude_conditions.append((k, v))

        if exclude_conditions:
            data["exclude_conditions"] = exclude_conditions

        return data


class TimeChartOutputSLZ(serializers.Serializer):
    series = serializers.ListField(child=serializers.IntegerField(), help_text="时间序列")
    timeline = serializers.ListField(child=serializers.IntegerField(), help_text="时间轴")

    class Meta:
        ref_name = "apigateway.apis.web.access_log.serializers.TimeChartOutputSLZ"


class RequestLogOutputSLZ(serializers.Serializer):
    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求 ID")
    timestamp = serializers.IntegerField(required=False, allow_null=True, help_text="请求时间戳")

    stage = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="环境")
    resource_id = serializers.IntegerField(required=False, allow_null=True, help_text="资源 ID")
    resource_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="资源名称")

    app_code = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="应用编码")
    client_ip = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="客户端 IP")
    method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求方法")
    http_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求域名")
    http_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求路径")
    params = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求参数")
    body = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求体")

    backend_scheme = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求协议")
    backend_method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求方法")
    backend_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求域名")
    backend_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求路径")
    response_body = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="响应体")
    status = serializers.IntegerField(required=False, allow_null=True, help_text="响应状态码")

    request_duration = serializers.IntegerField(required=False, allow_null=True, help_text="请求耗时")
    backend_duration = serializers.IntegerField(required=False, allow_null=True, help_text="后端请求耗时")

    code_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="状态码名称")
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="错误")
    response_desc = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="响应描述")

    class Meta:
        ref_name = "apigateway.apis.web.access_log.serializers.RequestLogOutputSLZ"


class LogLinkOutputSLZ(serializers.Serializer):
    link = serializers.CharField(read_only=True, help_text="链接地址")

    class Meta:
        ref_name = "apigateway.apis.web.access_log.serializers.LogLinkOutputSLZ"


class LogDetailQueryInputSLZ(serializers.Serializer):
    bk_nonce = serializers.IntegerField(help_text="随机数")
    bk_timestamp = serializers.IntegerField(help_text="时间戳")
    bk_signature = serializers.CharField(help_text="签名")
    shared_by = serializers.CharField(help_text="分享人")

    class Meta:
        ref_name = "apigateway.apis.web.access_log.serializers.LogDetailQueryInputSLZ"
