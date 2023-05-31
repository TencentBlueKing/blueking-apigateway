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

from django.utils.translation import ugettext_lazy as _


class _SystemDocCategoryEnum(Enum):
    DEFAULT = "默认分类"
    USER_BASE_SERVICE = "基础用户服务"
    CONFIG_SERVICE = "配置管理"
    HOST_MANAGEMENT = "主机管控"
    MANAGEMENT_TOOLS = "管理工具"


_BK_SYSTEMS = {
    "BK_LOGIN": {
        "name": "BK_LOGIN",
        "label": _("蓝鲸统一登录"),
        "remark": _("蓝鲸统一登录，管理用户登录验证，及用户信息"),
    },
    "BK_PAAS": {
        "name": "BK_PAAS",
        "label": _("蓝鲸开发者中心"),
        "remark": _("蓝鲸开发者中心"),
    },
    "CC": {
        "name": "CC",
        "label": _("蓝鲸配置平台"),
        "remark": _("蓝鲸配置平台是一款面向应用的CMDB，在ITIL体系里，CMDB是构建其它流程的基石，而在蓝鲸智云体系里，配置平台就扮演着基石的角色，为应用提供了各种运维场景的配置数据服务。"),
    },
    "GSE": {
        "name": "GSE",
        "label": _("蓝鲸管控平台"),
        "remark": _("蓝鲸管控平台"),
    },
    "JOB": {
        "name": "JOB",
        "label": _("蓝鲸作业平台V2(不推荐)"),
        "remark": _(
            "作业平台（Job）是一套基于蓝鲸智云管控平台Agent管道之上的基础操作平台，具备大并发处理能力；"
            "除了支持脚本执行、文件拉取/分发、定时任务等一系列可实现的基础运维场景以外，"
            "还运用流程化的理念很好的将零碎的单个任务组装成一个作业流程；"
            "而每个任务都可做为一个原子节点，提供给其它系统和平台调度，实现调度自动化。"
        ),
    },
    "JOBV3": {
        "name": "JOBV3",
        "label": _("蓝鲸作业平台V3"),
        "remark": _(
            "作业平台（Job）是一套基于蓝鲸智云管控平台Agent管道之上的基础操作平台，"
            "具备大并发处理能力；除了支持脚本执行、文件拉取/分发、定时任务等一系列可实现的基础运维场景以外，"
            "还运用流程化的理念很好的将零碎的单个任务组装成一个作业流程；"
            "而每个任务都可做为一个原子节点，提供给其它系统和平台调度，实现调度自动化。"
        ),
    },
    "CMSI": {
        "name": "CMSI",
        "label": _("蓝鲸消息管理"),
        "remark": _("蓝鲸消息管理，用于支持向用户发送多种类型的消息，包括邮件、短信、语音通知等"),
    },
    "SOPS": {
        "name": "SOPS",
        "label": _("标准运维"),
        "remark": _("标准运维"),
    },
    "MONITOR": {
        "name": "MONITOR",
        "label": _("监控平台"),
        "remark": _("监控平台"),
    },
    "MONITOR_V3": {
        "name": "MONITOR_V3",
        "label": _("监控平台V3"),
        "remark": _("监控平台V3"),
    },
    "USERMANAGE": {
        "name": "USERMANAGE",
        "label": _("用户管理"),
        "remark": _("用户管理"),
    },
    "ESB": {
        "name": "ESB",
        "label": _("API网关"),
        "remark": _("API网关"),
    },
    "ITSM": {
        "name": "ITSM",
        "label": _("流程服务"),
        "remark": _("流程服务"),
    },
    "LOG_SEARCH": {
        "name": "LOG_SEARCH",
        "label": _("日志平台"),
        "remark": _("日志平台"),
    },
    "BK_LOG": {
        "name": "BK_LOG",
        "label": _("日志平台"),
        "remark": _("日志平台"),
    },
    "IAM": {
        "name": "IAM",
        "label": _("权限中心"),
        "remark": _("权限中心"),
    },
    "BK_DOCS_CENTER": {
        "name": "BK_DOCS_CENTER",
        "label": _("文档中心"),
        "remark": _("文档中心"),
    },
    "DATA": {
        "name": "DATA",
        "label": _("基础计算平台"),
        "remark": _("基础计算平台"),
    },
    "BSCP": {
        "name": "BSCP",
        "label": _("蓝鲸基础服务配置平台"),
        "remark": _("蓝鲸基础服务配置平台"),
    },
}
