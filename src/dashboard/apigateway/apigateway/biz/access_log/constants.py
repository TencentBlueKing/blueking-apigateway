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
import re

from django.utils.translation import gettext_lazy as _

ES_LOG_FIELDS = [
    {
        "label": _("请求ID"),
        "field": "request_id",
        "is_filter": True,
    },
    {
        "label": _("请求时间"),
        "field": "timestamp",
        "is_filter": False,
    },
    {
        "label": _("蓝鲸应用"),
        "field": "app_code",
        "is_filter": True,
    },
    {
        "label": _("蓝鲸用户"),
        "field": "bk_username",
        "is_filter": True,
    },
    {
        "label": _("客户端IP"),
        "field": "client_ip",
        "is_filter": True,
    },
    {
        "label": _("环境"),
        "field": "stage",
        "is_filter": True,
    },
    {
        "label": _("资源ID"),
        "field": "resource_id",
        "is_filter": True,
    },
    {
        "label": _("资源名称"),
        "field": "resource_name",
        "is_filter": True,
    },
    {
        "label": _("请求方法"),
        "field": "method",
        "is_filter": True,
    },
    {
        "label": _("请求域名"),
        "field": "http_host",
        "is_filter": True,
    },
    {
        "label": _("请求路径"),
        "field": "http_path",
        "is_filter": True,
    },
    {
        "label": "QueryString",
        "field": "params",
        "is_filter": True,
    },
    {
        "label": "Body",
        "field": "body",
        "is_filter": True,
    },
    {
        "label": _("后端请求方法"),
        "field": "backend_method",
        "is_filter": True,
    },
    {
        "label": _("后端Scheme"),
        "field": "backend_scheme",
        "is_filter": True,
    },
    {
        "label": _("后端域名"),
        "field": "backend_host",
        "is_filter": True,
    },
    {
        "label": _("后端路径"),
        "field": "backend_path",
        "is_filter": True,
    },
    {
        "label": _("响应正文"),
        "field": "response_body",
        "is_filter": True,
    },
    {
        "label": _("响应体大小"),
        "field": "response_size",
        "is_filter": True,
    },
    {
        "label": _("状态码"),
        "field": "status",
        "is_filter": True,
    },
    # {
    #     "label": _("请求头"),
    #     "field": "headers",
    #     "is_filter": False,
    # },
    {
        "label": _("请求总耗时"),
        "field": "request_duration",
        "is_filter": True,
    },
    {
        "label": _("请求后端耗时"),
        "field": "backend_duration",
        "is_filter": True,
    },
    {
        "label": _("错误编码名称"),
        "field": "code_name",
        "is_filter": True,
    },
    {
        "label": "Error",
        "field": "error",
        "is_filter": False,
    },
    {
        "label": _("响应说明"),
        "field": "response_desc",
        "is_filter": False,
    },
]


# ES_QUERY_FIELDS = [field["field"] for field in ES_LOG_FIELDS if field["is_filter"]]


ES_OUTPUT_FIELDS = [field["field"] for field in ES_LOG_FIELDS]


# 完全匹配的敏感 key，如 key access_token 仅匹配字段 access_token
SENSITIVE_KEYS = [
    # apigateway sensitive keys
    "skey",
    "openkey",
    "auth_token",
    "access_token",
    "bk_token",
    "bk_ticket",
    "oa_ticket",
    "app_secret",
    "signature",
    "bk_nonce",
    "bk_timestamp",
    "bk_app_secret",
    "bk_signature",
]


# 部分匹配的敏感 key，如 key password 匹配字段 my_password
SENSITIVE_KEYS_PART_MATCH = [
    # sentry Server-Side Scrubbing, https://docs.sentry.io/data-management/sensitive-data/#server-side-scrubbing
    "password",
    "secret",
    "passwd",
    "api_key",
    "apikey",
    "credentials",
    "mysql_pwd",
    "stripetoken",
]


SENSITIVE_KEYS_MATCH_PATTERN = re.compile(r"\b(%s)\b" % "|".join(SENSITIVE_KEYS))
SENSITIVE_KEYS_PART_MATCH_PATTERN = re.compile(r"(%s)" % "|".join(SENSITIVE_KEYS_PART_MATCH))


LOG_LINK_EXPIRE_SECONDS = 24 * 60 * 60

LOG_LINK_SHARED_PATH = "/{gateway_id}/access-log/{request_id}/"
