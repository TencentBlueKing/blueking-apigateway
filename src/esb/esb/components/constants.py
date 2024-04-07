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


class SystemDocCategoryEnum(Enum):
    DEFAULT = "默认分类"
    USER_BASE_SERVICE = "基础用户服务"
    CONFIG_SERVICE = "配置管理"
    HOST_MANAGEMENT = "主机管控"
    MANAGEMENT_TOOLS = "管理工具"


SYSTEM_DOC_CATEGORY = [
    {
        "name": "default",
        "label": SystemDocCategoryEnum.DEFAULT.value,
        "label_en": "Default",
        "priority": 9000,
        "systems": [],
    },
    {
        "name": "user_base_service",
        "label": SystemDocCategoryEnum.USER_BASE_SERVICE.value,
        "label_en": "Basic User Service",
        "priority": 8900,
        "systems": [],
    },
    {
        "name": "config_service",
        "label": SystemDocCategoryEnum.CONFIG_SERVICE.value,
        "label_en": "Configuration Management",
        "priority": 8800,
        "systems": [],
    },
    {
        "name": "host_management",
        "label": SystemDocCategoryEnum.HOST_MANAGEMENT.value,
        "label_en": "Host Management",
        "priority": 8700,
        "systems": [],
    },
    {
        "name": "management_tools",
        "label": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
        "label_en": "Management Tools",
        "priority": 8600,
        "systems": [],
    },
]


BK_SYSTEMS = {
    "BK_LOGIN": {
        "name": "BK_LOGIN",
        "label": _("蓝鲸统一登录"),
        "label_en": "BK Login",
        "remark": _("蓝鲸统一登录，管理用户登录验证，及用户信息"),
        "remark_en": "BlueKing Login System, managing user login authentication and user information",
        "doc_category": SystemDocCategoryEnum.USER_BASE_SERVICE.value,
    },
    "CC": {
        "name": "CC",
        "label": _("蓝鲸配置平台"),
        "label_en": "Configuration System",
        "remark": _(
            "蓝鲸配置平台是一款面向应用的CMDB，在ITIL体系里，CMDB是构建其它流程的基石，而在蓝鲸智云体系里，配置平台就扮演着基石的角色，为应用提供了各种运维场景的配置数据服务。"
        ),
        "remark_en": (
            "The BlueKing Configuration System is an application-oriented CMDB. In the "
            "ITIL system, CMDB is the cornerstone for building other processes, while in "
            "BlueKing cloud system, the configuration system serves as a cornerstone and "
            "provides app with configuration data services in various O&M scenarios."
        ),
        "doc_category": SystemDocCategoryEnum.CONFIG_SERVICE.value,
    },
    "JOBV3": {
        "name": "JOBV3",
        "label": _("蓝鲸作业平台V3"),
        "label_en": "BK Job V3",
        "remark": _(
            "作业平台（Job）是一套基于蓝鲸智云管控平台Agent管道之上的基础操作平台，具备大并发处理能力；"
            "除了支持脚本执行、文件拉取/分发、定时任务等一系列可实现的基础运维场景以外，"
            "还运用流程化的理念很好的将零碎的单个任务组装成一个作业流程；"
            "而每个任务都可做为一个原子节点，提供给其它系统和平台调度，实现调度自动化。"
        ),
        "remark_en": (
            "BlueKing Job System (Job) is a set of basic operating platform based on the "
            "BlueKing cloud control platform Agent channel, presenting a large concurrent "
            "processing capability; in addition to a series of achievable basic O&M "
            "scenarios such as script execution, file pull / dispatch, and scheduled "
            "tasks, it also depends on the concept of process flow to assemble fragmented "
            "individual tasks into a single workflow; each task can be used as an atomic "
            "node to provide to other systems and platforms for dispatching, so as to "
            "achieve automated dispatching."
        ),
        "doc_category": SystemDocCategoryEnum.HOST_MANAGEMENT.value,
    },
    "CMSI": {
        "name": "CMSI",
        "label": _("蓝鲸消息管理"),
        "label_en": "Message Management",
        "remark": _("蓝鲸消息管理，用于支持向用户发送多种类型的消息，包括邮件、短信、语音通知等"),
        "remark_en": (
            "BlueKing Message Management, used for sending various types of messages to "
            "the user, including email, SMS, voice notification etc."
        ),
        "doc_category": SystemDocCategoryEnum.USER_BASE_SERVICE.value,
    },
    "SOPS": {
        "name": "SOPS",
        "label": _("标准运维"),
        "label_en": "Standard OPS",
        "remark": _("标准运维"),
        "remark_en": "Standard OPS",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
    },
    "MONITOR_V3": {
        "name": "MONITOR_V3",
        "label": _("监控平台V3"),
        "label_en": "Monitor V3",
        "remark": _("监控平台V3"),
        "remark_en": "Monitor V3",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
    },
    "USERMANAGE": {
        "name": "USERMANAGE",
        "label": _("用户管理"),
        "label_en": "User Management",
        "remark": _("用户管理"),
        "remark_en": "User Management",
        "doc_category": SystemDocCategoryEnum.USER_BASE_SERVICE.value,
    },
    "ITSM": {
        "name": "ITSM",
        "label": _("流程服务"),
        "label_en": "ITSM",
        "remark": _("流程服务"),
        "remark_en": "ITSM",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
    },
    "BK_LOG": {
        "name": "BK_LOG",
        "label": _("日志平台"),
        "label_en": "BK Log",
        "remark": _("日志平台"),
        "remark_en": "BK Log",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
    },
    "IAM": {
        "name": "IAM",
        "label": _("权限中心"),
        "label_en": "IAM",
        "remark": _("权限中心"),
        "remark_en": "IAM",
        "doc_category": SystemDocCategoryEnum.USER_BASE_SERVICE.value,
    },
    "BSCP": {
        "name": "BSCP",
        "label": _("蓝鲸基础服务配置平台"),
        "label_en": "BSCP",
        "remark": _("蓝鲸基础服务配置平台"),
        "remark_en": "BSCP",
        "doc_category": SystemDocCategoryEnum.CONFIG_SERVICE.value,
    },
    "DATA": {
        "name": "DATA",
        "label": _("基础计算平台"),
        "label_en": "BK Base",
        "remark": _("基础计算平台"),
        "remark_en": "BK Base",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
    },
    "GSE": {
        "name": "GSE",
        "label": _("蓝鲸管控平台"),
        "label_en": "Control System",
        "remark": _("蓝鲸管控平台"),
        "remark_en": "Control System",
        "doc_category": SystemDocCategoryEnum.HOST_MANAGEMENT.value,
    },
    # not public
    "APPROVAL": {
        "name": "APPROVAL",
        "label": "APPROVAL",
        "label_en": "APPROVAL",
        "remark": "APPROVAL",
        "remark_en": "APPROVAL",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "AUTH": {
        "name": "AUTH",
        "label": "AUTH",
        "label_en": "AUTH",
        "remark": "AUTH",
        "remark_en": "AUTH",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "BK_DOCS_CENTER": {
        "name": "BK_DOCS_CENTER",
        "label": _("文档中心"),
        "label_en": "Docs Center",
        "remark": _("文档中心"),
        "remark_en": "Docs Center",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "BK_PAAS": {
        "name": "BK_PAAS",
        "label": _("蓝鲸开发者中心"),
        "label_en": "Developer Center",
        "remark": _("蓝鲸开发者中心"),
        "remark_en": "Developer Center",
        "doc_category": SystemDocCategoryEnum.USER_BASE_SERVICE.value,
        "is_public": False,
    },
    "CICDKIT": {
        "name": "CICDKIT",
        "label": "CICDKIT",
        "label_en": "CICDKIT",
        "remark": "CICDKIT",
        "remark_en": "CICDKIT",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "DEVOPS": {
        "name": "DEVOPS",
        "label": "DEVOPS",
        "label_en": "DEVOPS",
        "remark": "DEVOPS",
        "remark_en": "DEVOPS",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "FTA": {
        "name": "FTA",
        "label": "FTA",
        "label_en": "FTA",
        "remark": "FTA",
        "remark_en": "FTA",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "HEARTBEAT": {
        "name": "HEARTBEAT",
        "label": "HEARTBEAT",
        "label_en": "HEARTBEAT",
        "remark": "HEARTBEAT",
        "remark_en": "HEARTBEAT",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "JOB": {
        "name": "JOB",
        "label": _("蓝鲸作业平台V2(不推荐)"),
        "label_en": "BK Job V2(Deprecated)",
        "remark": _(
            "作业平台（Job）是一套基于蓝鲸智云管控平台Agent管道之上的基础操作平台，具备大并发处理能力；"
            "除了支持脚本执行、文件拉取/分发、定时任务等一系列可实现的基础运维场景以外，"
            "还运用流程化的理念很好的将零碎的单个任务组装成一个作业流程；"
            "而每个任务都可做为一个原子节点，提供给其它系统和平台调度，实现调度自动化。"
        ),
        "remark_en": (
            "BlueKing Job System (Job) is a set of basic operating platform based on the "
            "BlueKing cloud control platform Agent channel, presenting a large concurrent "
            "processing capability; in addition to a series of achievable basic O&M "
            "scenarios such as script execution, file pull / dispatch, and scheduled "
            "tasks, it also depends on the concept of process flow to assemble fragmented "
            "individual tasks into a single workflow; each task can be used as an atomic "
            "node to provide to other systems and platforms for dispatching, so as to "
            "achieve automated dispatching."
        ),
        "doc_category": SystemDocCategoryEnum.HOST_MANAGEMENT.value,
        "is_public": False,
    },
    "MONITOR": {
        "name": "MONITOR",
        "label": "MONITOR",
        "label_en": "MONITOR",
        "remark": "MONITOR",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
        "is_public": False,
    },
    "ESB": {
        "name": "ESB",
        "label": _("API网关"),
        "label_en": "API Gateway",
        "remark": _("API网关"),
        "remark_en": "API Gateway",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
        "is_public": False,
    },
    # LOG_SEARCH is deprecated
    "LOG_SEARCH": {
        "name": "LOG_SEARCH",
        "label": _("日志平台"),
        "label_en": "BK Log",
        "remark": _("日志平台"),
        "remark_en": "BK Log",
        "doc_category": SystemDocCategoryEnum.MANAGEMENT_TOOLS.value,
        "is_public": False,
    },
    "WEIXIN": {
        "name": "WEIXIN",
        "label": "WEIXIN",
        "label_en": "WEIXIN",
        "remark": "WEIXIN",
        "remark_en": "WEIXIN",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
        "is_public": False,
    },
    "NODEMAN": {
        "name": "NODEMAN",
        "label": "NODEMAN",
        "label_en": "NODEMAN",
        "remark": "NODEMAN",
        "remark_en": "NODEMAN",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
    },
    "GSEKIT": {
        "name": "GSEKIT",
        "label": "GSEKIT",
        "label_en": "GSEKIT",
        "remark": "GSEKIT",
        "remark_en": "GSEKIT",
        "doc_category": SystemDocCategoryEnum.DEFAULT.value,
    },
}
