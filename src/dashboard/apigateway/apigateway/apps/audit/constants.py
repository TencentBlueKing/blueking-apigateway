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

from django.utils.translation import gettext_lazy as _

from apigateway.common.constants import ChoiceEnum


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


class OpObjectTypeEnum(ChoiceEnum):
    API = "api"
    STAGE = "stage"
    RESOURCE = "resource"
    RESOURCE_VERSION = "resource_version"
    RELEASE = "release"
    IP_GROUP = "ip_group"
    API_LABEL = "api_label"
    MICRO_GATEWAY = "micro_gateway"
    PLUGIN = "plugin"


AUDIT_SYSTEM = "apigateway-dashboard"
