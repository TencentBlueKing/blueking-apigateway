#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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


class SkillTypeEnum(StructuredEnum):
    """Skill 来源类型"""

    PLATFORM = EnumField("platform", label=_("平台内置"))
    GATEWAY = EnumField("gateway", label=_("网关"))


class SkillStatusEnum(StructuredEnum):
    """Skill 状态"""

    UNPUBLISHED = EnumField("unpublished", label=_("未发布"))
    PUBLISHED = EnumField("published", label=_("已发布"))
    OFFLINE = EnumField("offline", label=_("已下架"))


# 对外 ID（skill_id）的来源前缀
SKILL_ID_PREFIXES = {
    SkillTypeEnum.PLATFORM.value: "p_",
    SkillTypeEnum.GATEWAY.value: "g_",
}

# artifact 中 SKILL.md 正文的键，键为包内相对路径
SKILL_MD_ARTIFACT_KEY = "SKILL.md"

# code 存对外 ID：前缀 2 + 网关名最长 64 + 下划线 1 + name 最长 64 = 131
SKILL_CODE_MAX_LENGTH = 160
SKILL_NAME_MAX_LENGTH = 64
SKILL_DISPLAY_NAME_MAX_LENGTH = 64
SKILL_DESCRIPTION_MAX_LENGTH = 1024
SKILL_VERSION_MAX_LENGTH = 64
SKILL_TAG_NAME_MAX_LENGTH = 64
