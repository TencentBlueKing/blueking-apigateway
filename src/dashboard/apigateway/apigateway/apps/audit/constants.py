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
from enum import Enum

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _


class OpTypeEnum(Enum):
    QUERY = "query"
    CREATE = "create"
    DELETE = "delete"
    MODIFY = "modify"


OP_TYPE_CHOICES = (
    (OpTypeEnum.QUERY.value, _("查询")),
    (OpTypeEnum.CREATE.value, _("创建")),
    (OpTypeEnum.DELETE.value, _("删除")),
    (OpTypeEnum.MODIFY.value, _("修改")),
)


class OpStatusEnum(Enum):
    SUCCESS = "success"
    FAIL = "fail"
    UNKNOWN = "unknown"


OP_STATUS_CHOICES = (
    (OpStatusEnum.SUCCESS.value, _("成功")),
    (OpStatusEnum.FAIL.value, _("失败")),
    (OpStatusEnum.UNKNOWN.value, _("未知")),
)


class OpObjectTypeEnum(StructuredEnum):
    GATEWAY = EnumField("gateway")
    STAGE = EnumField("stage")
    RESOURCE = EnumField("resource")
    RESOURCE_VERSION = EnumField("resource_version")
    RELEASE = EnumField("release")
    ACCESS_STRATEGY = EnumField("access_strategy")
    IP_GROUP = EnumField("ip_group")
    GATEWAY_LABEL = EnumField("gateway_label")
    MICRO_GATEWAY = EnumField("micro_gateway")
    PLUGIN = EnumField("plugin")
    RESOURCE_DOC = EnumField("resource_doc")


AUDIT_SYSTEM = "apigateway-dashboard"
