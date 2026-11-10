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
import re
from pathlib import Path

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.conf import settings

# Agent Skills 规范名：小写字母、数字、单个连字符，1–64，不以连字符开头或结尾；步骤名同规则
SKILL_NAME_PATTERN = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
SKILL_STEP_NAME_PATTERN = SKILL_NAME_PATTERN

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

SKILL_BODY_MAX_LINES = 500

SKILL_FILE_NAME = "SKILL.md"

SKILL_DATA_DIR = Path(settings.SKILL_DATA_DIR)
SKILL_TEMPLATES_DIR = SKILL_DATA_DIR / "templates"
SKILL_DECLARATIONS_DIR = SKILL_DATA_DIR / "declarations"
SKILL_BODY_TEMPLATE_NAME = "SKILL.md.j2"


class SkillSyncStatusEnum(StructuredEnum):
    """内置 Skill 单条注入的结果"""

    CREATED = EnumField("created", label="新建")
    NEW_VERSION = EnumField("new_version", label="新版本")
    SKIPPED_SAME_VERSION = EnumField("skipped_same_version", label="跳过（同版本）")
    SKIPPED_MISSING_RESOURCES = EnumField("skipped_missing_resources", label="跳过（资源缺失）")
    REJECTED = EnumField("rejected", label="拒绝")
    FAILED = EnumField("failed", label="失败")
