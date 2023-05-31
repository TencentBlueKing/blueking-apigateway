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
from apigateway.utils.yaml import YamlRepresenterEnum


class UpstreamHashOnEnum(str, YamlRepresenterEnum):
    VARS = "vars"
    HEADER = "header"
    COOKIE = "cookie"
    CONSUMER = "consumer"


class UpstreamTypeEnum(str, YamlRepresenterEnum):
    ROUNDROBIN = "roundrobin"
    CHASH = "chash"


class UpstreamSchemeEnum(str, YamlRepresenterEnum):
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    GRPCS = "grpcs"
    TCP = "tcp"
    UDP = "udp"
    TLS = "tls"


class UpstreamPassHostEnum(str, YamlRepresenterEnum):
    PASS = "pass"
    NODE = "node"
    REWRITE = "rewrite"


class UpstreamCheckActiveTypeEnum(str, YamlRepresenterEnum):
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"


class ResourceRewriteHeadersStrategyEnum(str, YamlRepresenterEnum):
    APPEND = "append"  # 追加
    INHERIT = "inherit"  # 继承
    OVERRIDE = "override"  # 重写


class ResourceProtocolEnum(str, YamlRepresenterEnum):
    HTTP = "http"
    TCP = "tcp"
    GRPC = "grpc"


class HttpResourceMethodEnum(str, YamlRepresenterEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"
