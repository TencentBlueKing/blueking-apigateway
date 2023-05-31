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


class SystemDocCategoryEnum(StructuredEnum):
    DEFAULT = EnumField("默认分类")
    USER_BASE_SERVICE = EnumField("基础用户服务")
    CONFIG_SERVICE = EnumField("配置管理")
    HOST_MANAGEMENT = EnumField("主机管控")
    MANAGEMENT_TOOLS = EnumField("管理工具")


BK_SYSTEMS = [
    "BK_LOGIN",
    "BK_PAAS",
    "CC",
    "GSE",
    "JOB",
    "JOBV3",
    "CMSI",
    "SOPS",
    "MONITOR",
    "MONITOR_V3",
    "USERMANAGE",
    "ESB",
    "ITSM",
    "LOG_SEARCH",
    "IAM",
    "BK_DOCS_CENTER",
    "DATA",
    "BSCP",
]
