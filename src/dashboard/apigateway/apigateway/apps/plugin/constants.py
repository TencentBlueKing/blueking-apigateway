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

from apigateway.core.constants import ScopeTypeEnum


class PluginTypeEnum(StructuredEnum):
    IP_RESTRICTION = EnumField("ip-restriction", label=_("IP访问控制"))
    RATE_LIMIT = EnumField("rate_limit", label=_("频率控制"))
    CORS = EnumField("cors", label="CORS")
    # CIRCUIT_BREAKER = EnumField("circuit_breaker", label=_("断路器"))
    VERIFIED_USER_EXEMPTED_APPS = EnumField("bk-verified-user-exempted-apps", label=_("免用户认证应用白名单"))


class PluginTypeCodeEnum(StructuredEnum):
    BK_RATE_LIMIT = EnumField("bk-rate-limit", label=_("频率控制"))
    BK_CORS = EnumField("bk-cors", label="CORS")
    BK_HEADER_REWRITE = EnumField("bk-header-rewrite", label=_("Header 转换"))
    BK_IP_RESTRICTION = EnumField("bk-ip-restriction", label="ip-restriction")
    BK_STATUS_REWRITE = EnumField("bk-status-rewrite", label=_("网关错误使用HTTP状态码200(不推荐)"))
    BK_VERIFIED_USER_EXEMPTED_APPS = EnumField(
        "bk-verified-user-exempted-apps", label=_("免用户认证应用白名单(不推荐)")
    )


class PluginTypeScopeEnum(StructuredEnum):
    STAGE = EnumField(ScopeTypeEnum.STAGE.value, label=_("环境"))
    RESOURCE = EnumField(ScopeTypeEnum.RESOURCE.value, label=_("资源"))
    STAGE_AND_RESOURCE = EnumField("stage_and_resource", label=_("环境和资源"))
    # maybe more enum: gateway, all


class PluginBindingScopeEnum(StructuredEnum):
    STAGE = EnumField(ScopeTypeEnum.STAGE.value, label=_("环境"))
    RESOURCE = EnumField(ScopeTypeEnum.RESOURCE.value, label=_("资源"))


class PluginStyleEnum(StructuredEnum):
    RAW = EnumField("raw", label=_("原生"))
    DYNAMIC = EnumField("dynamic", label=_("动态"))
    FIX = EnumField("fix", label=_("固定"))


class PluginBindingSourceEnum(StructuredEnum):
    YAML_IMPORT = EnumField("yaml_import", label=_("yaml导入"))
    USER_CREATE = EnumField("user_create", label=_("用户创建"))
