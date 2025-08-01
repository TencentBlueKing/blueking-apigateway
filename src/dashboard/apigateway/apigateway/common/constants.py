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
import re

from blue_krill.data_types.enum import EnumField, StructuredEnum

CACHE_TIME_5_MINUTES = 5 * 60
CACHE_TIME_24_HOURS = 24 * 3600

CACHE_MAXSIZE = 2000


class LanguageCodeEnum(StructuredEnum):
    EN = EnumField("en", "en")
    ZH_HANS = EnumField("zh-hans", "zh-hans")


# IP 或 IP 网段正则
# IPV4 + mask
# IP_OR_SEGMENT_PATTERN = re.compile(
#     r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/([1-2][0-9]|3[0-2]|[1-9]))?$"
# )

# IPV4/IPV6 + mask
# 参考：https://www.w3cschool.cn/notebook/notebook-jghl2tn5.html
# IP_OR_SEGMENT_PATTERN = re.compile(
#     r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/(\d|[1-2]\d|3[0-2]))?$|^([\da-fA-F]{1,4}:){6}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^::([\da-fA-F]{1,4}:){0,4}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:):([\da-fA-F]{1,4}:){0,3}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){2}:([\da-fA-F]{1,4}:){0,2}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){3}:([\da-fA-F]{1,4}:){0,1}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){4}:((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){7}[\da-fA-F]{1,4}(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^:((:[\da-fA-F]{1,4}){1,6}|:)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^[\da-fA-F]{1,4}:((:[\da-fA-F]{1,4}){1,5}|:)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){2}((:[\da-fA-F]{1,4}){1,4}|:)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){3}((:[\da-fA-F]{1,4}){1,3}|:)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){4}((:[\da-fA-F]{1,4}){1,2}|:)(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){5}:([\da-fA-F]{1,4})?(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$|^([\da-fA-F]{1,4}:){6}:(\/([1-9]?\d|(1([0-1]\d|2[0-8]))))?$"  # noqa
# )

HEADER_BKAPI_AUTHORIZATION = "X-Bkapi-Authorization"

# release gateway interval
RELEASE_GATEWAY_INTERVAL_SECOND = 15

# 网关名正则
GATEWAY_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,29}$")


# 用户认证类型
class UserAuthTypeEnum(StructuredEnum):
    IEOD = EnumField("ieod")
    TENCENT = EnumField("tencent")
    DEFAULT = EnumField("default")


# 网关文档维护者类型
class GatewayAPIDocMaintainerTypeEnum(StructuredEnum):
    USER = EnumField("user", label="用户")
    SERVICE_ACCOUNT = EnumField("service_account", label="服务号")


DOMAIN_WITH_HTTP_AND_IPV6_PATTERN = re.compile(
    r"^http(s)?:\/\/\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?\/?$"
)

DOMAIN_PATTERN = re.compile(
    r"^(?=^.{3,255}$)http(s)?:\/\/[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?\/?$"
    + "|"
    + DOMAIN_WITH_HTTP_AND_IPV6_PATTERN.pattern
)

HEADER_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9-]{1,100}$")

STAGE_VAR_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,49}$")


# 调用来源类型
class CallSourceTypeEnum(StructuredEnum):
    OpenAPI = EnumField("openapi")
    Web = EnumField("web")
