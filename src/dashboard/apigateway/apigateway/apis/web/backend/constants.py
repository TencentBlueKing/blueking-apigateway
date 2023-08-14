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
import re

from blue_krill.data_types.enum import EnumField, StructuredEnum

from apigateway.core.constants import BackendTypeEnum

BACKEND_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,19}$")


class BackendConfigTypeEnum(StructuredEnum):
    NODE = EnumField("node", label="节点")
    # NOTE: 当前不支持
    SERVICE_DISCOVERY = EnumField("service_discovery", label="服务发现")


class LoadBalanceTypeEnum(StructuredEnum):
    RR = EnumField("roundrobin", "RR")
    WRR = EnumField("weighted-roundrobin", "Weighted-RR")


class BackendConfigSchemaEnum(StructuredEnum):
    # for http type backend
    HTTP = EnumField("http", label="HTTP")
    HTTPS = EnumField("https", label="HTTPS")
    # for grpc type backend
    GRPC = EnumField("grpc", label="GRPC")
    GRPCS = EnumField("grpcs", label="GRPCS")


BACKEND_CONFIG_SCHEMA_MAP = {
    BackendTypeEnum.HTTP.value: [BackendConfigSchemaEnum.HTTP.value, BackendConfigSchemaEnum.HTTPS.value],
    BackendTypeEnum.GRPC.value: [BackendConfigSchemaEnum.GRPC.value, BackendConfigSchemaEnum.GRPCS.value],
}
