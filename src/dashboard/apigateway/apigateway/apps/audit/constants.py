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


class OpTypeEnum(StructuredEnum):
    CREATE = EnumField("create", label=_("创建"))
    DELETE = EnumField("delete", label=_("删除"))
    MODIFY = EnumField("modify", label=_("修改"))
    QUERY = EnumField("query", label=_("查询"))


class OpStatusEnum(StructuredEnum):
    SUCCESS = EnumField("success", label=_("成功"))
    FAIL = EnumField("fail", label=_("失败"))
    UNKNOWN = EnumField("unknown", label=_("未知"))


class OpObjectTypeEnum(StructuredEnum):
    GATEWAY = EnumField("gateway", label=_("网关"))
    STAGE = EnumField("stage", label=_("环境"))
    BACKEND = EnumField("backend", label=_("后端服务"))
    STAGE_BACKEND = EnumField("stage_backend", label=_("环境后端配置"))
    RESOURCE = EnumField("resource", label=_("资源"))
    RESOURCE_VERSION = EnumField("resource_version", label=_("资源版本"))
    RELEASE = EnumField("release", label=_("发布"))
    GATEWAY_LABEL = EnumField("gateway_label", label=_("网关标签"))
    MICRO_GATEWAY = EnumField("micro_gateway", label=_("微网关"))
    PLUGIN = EnumField("plugin", label=_("插件"))
    RESOURCE_DOC = EnumField("resource_doc", label=_("资源文档"))
    GATEWAY_MEMBER = EnumField("gateway_member", label=_("网关成员"))


# for translation only
COMMENTS = (
    _("创建网关"),
    _("更新网关"),
    _("删除网关"),
    _("创建网关标签"),
    _("更新网关标签"),
    _("删除网关标签"),
    _("创建资源文档"),
    _("更新资源文档"),
    _("删除资源文档"),
    _("创建资源"),
    _("更新资源"),
    _("删除资源"),
    _("创建后端服务"),
    _("更新后端服务"),
    _("删除后端服务"),
    _("创建微网关实例"),
    _("更新微网关实例"),
    _("删除微网关实例"),
    _("创建插件"),
    _("更新插件"),
    _("删除插件"),
    _("创建环境"),
    _("更新环境"),
    _("删除环境"),
    _("版本发布"),
    _("生成版本"),
    # extras
    _("环境状态变更"),
    _("更新环境变量"),
    _("批量更新资源"),
    _("批量删除资源"),
    _("创建环境后端配置"),
    _("更新环境后端配置"),
    _("删除环境后端配置"),
)
