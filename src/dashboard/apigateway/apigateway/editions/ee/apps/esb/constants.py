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
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

DEFAULT_DOC_CATEGORY = "默认分类"


def get_esb_board_config(board: str):
    board_configs = {
        "default": {
            "name": "default",
            "label": _("蓝鲸智云"),
            "should_display_label": False,
        },
    }
    return board_configs[board]


class DataTypeEnum(StructuredEnum):
    OFFICIAL_PUBLIC = EnumField(1, label=gettext_lazy("官方公开"))
    OFFICIAL_HIDDEN = EnumField(2, label=gettext_lazy("官方隐藏"))
    CUSTOM = EnumField(3, label=gettext_lazy("用户自定义"))

    @property
    def is_official(self):
        return self._value_ in [self.OFFICIAL_PUBLIC.value, self.OFFICIAL_HIDDEN.value]


class LanguageEnum(StructuredEnum):
    EN = EnumField("en", label="English")
    ZH_HANS = EnumField("zh-hans", label=gettext_lazy("简体中文"))


class MethodEnum(StructuredEnum):
    GET_POST = EnumField("", label="GET/POST")
    GET = EnumField("GET", label="GET")
    POST = EnumField("POST", label="POST")
    PUT = EnumField("PUT", label="PUT")
    PATCH = EnumField("PATCH", label="PATCH")
    DELETE = EnumField("DELETE", label="DELETE")


class FunctionControllerCodeEnum(StructuredEnum):
    SKIP_USER_AUTH = EnumField("user_auth::skip_user_auth", label=_("是否跳过用户身份验证"))
    JWT_KEY = EnumField("jwt::private_public_key", label=_("JWT私钥公钥"))


SYSTEM_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
CHANNEL_PATH_PATTERN = re.compile(r"^/[/a-zA-Z0-9_-]+$")
COMPONENT_CODENAME_PATTERN = re.compile(r"^[a-z][a-z0-9._]+[a-z0-9_]$")
COMPONENT_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class ComponentDocTypeEnum(StructuredEnum):
    MARKDOWN = EnumField("markdown", label="Markdown")
    HTML = EnumField("html", label="Html")
    RST = EnumField("rst", label="RST")
