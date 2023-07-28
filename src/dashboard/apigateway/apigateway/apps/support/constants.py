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

from apigateway.common.constants import ChoiceEnumMixin


class DocTypeEnum(ChoiceEnumMixin, Enum):
    MARKDOWN = "markdown"


class ProgrammingLanguageEnum(StructuredEnum):
    UNKNOWN = EnumField("unknown")
    PYTHON = EnumField("python")
    GOLANG = EnumField("golang")


class DocLanguageEnum(StructuredEnum):
    EN = EnumField("en", label=_("英文"))
    ZH = EnumField("zh", label=_("中文"))


class DocSourceEnum(StructuredEnum):
    IMPORT = EnumField("import", label=_("导入"))
    CUSTOM = EnumField("custom", label=_("自定义"))


class DocArchiveTypeEnum(StructuredEnum):
    TGZ = EnumField("tgz", label=_("tgz 归档文件"))
    ZIP = EnumField("zip", label=_("zip 归档文件"))
