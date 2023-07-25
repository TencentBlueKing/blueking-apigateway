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
from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _


class AlarmTypeEnum(StructuredEnum):
    RESOURCE_BACKEND = EnumField("resource_backend", label=_("请求资源后端错误"))
    APP_REQUEST = EnumField("app_request", label=_("蓝鲸应用请求错误"))
    NGINX_ERROR = EnumField("nginx_error", label=_("Nginx错误"))


class ResourceBackendAlarmSubTypeEnum(StructuredEnum):
    """请求后端告警子类型"""

    # 后端响应状态码5XX
    STATUS_CODE_5XX = EnumField("status_code_5xx", label=_("后端响应状态码5xx"))
    # 请求后端超时
    GATEWAY_TIMEOUT = EnumField("gateway_timeout", label=_("请求后端响应超时"))
    # 请求后端错误
    BAD_GATEWAY = EnumField("bad_gateway", label=_("请求后端错误"))


# 请求记录中错误的 code_name 与告警子类型映射关系
ERROR_CODE_NAME_TO_ALARM_SUBTYPE = {
    "ERROR_REQUESTING_RESOURCE": "bad_gateway",
    "REQUEST_BACKEND_TIMEOUT": "gateway_timeout",
    "REQUEST_RESOURCE_5xx": "status_code_5xx",
}


# 网关告警规则，可供网关管理员选择，以配置网关告警策略
API_ALARM_TYPE_CHOICES = [(AlarmTypeEnum.RESOURCE_BACKEND.value, _("请求资源后端错误"))]


class AlarmStatusEnum(StructuredEnum):
    RECEIVED = EnumField("received", label=_("已接收"))
    SKIPPED = EnumField("skipped", label=_("已忽略"))
    SUCCESS = EnumField("success", label=_("告警成功"))
    FAILURE = EnumField("failure", label=_("告警失败"))


class NoticeWayEnum(StructuredEnum):
    WECHAT = EnumField("wechat")
    IM = EnumField("im")
    MAIL = EnumField("mail")


class NoticeRoleEnum(StructuredEnum):
    MAINTAINER = EnumField("maintainer")


DETECT_METHOD_CHOICES = [
    ("gt", ">"),
    ("gte", ">="),
    ("lt", "<"),
    ("lte", "<="),
    ("eq", "="),
]


# 查询bkmonitor事件，及请求日志源数据的时间偏移量
SOURCE_TIME_OFFSET_SECONDS = 300


API_ERRORLOG_OUTPUT_FIELDS = [
    "api_id",
    "api_name",
    "stage",
    "resource_id",
    "app_code",
    "backend_scheme",
    "backend_method",
    "backend_host",
    "backend_path",
    "response_body",
    "method",
    "http_host",
    "http_path",
    "client_ip",
    "status",
    "error",
    "time",
    "request_id",
]


NGINX_ERROR_OUTPUT_FIELDS = [
    "serverIp",
    "log",
]


# AlarmRecord 告警记录保存时间
ALARM_RECORD_RETENTION_DAYS = 360


DEFAULT_SENDER = "blueking"
