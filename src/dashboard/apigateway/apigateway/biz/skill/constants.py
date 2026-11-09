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

# Agent Skills 规范名：小写字母、数字、单个连字符，1–64，不以连字符开头或结尾；步骤名同规则
SKILL_NAME_PATTERN = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
SKILL_STEP_NAME_PATTERN = SKILL_NAME_PATTERN
SKILL_DISPLAY_NAME_PATTERN = re.compile(r"^(?:[^\W_]|-)+(?: (?:[^\W_]|-)+)*$")
SKILL_DISPLAY_NAME_EN_PATTERN = re.compile(r"^[A-Za-z0-9-]+(?: [A-Za-z0-9-]+)*$")

# 资源文档里列为必填的认证凭据，由调用方按登录态注入，不进参数映射
CREDENTIAL_PARAMS = frozenset({"access_token", "bk_token", "bk_ticket", "bk_app_secret"})
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

SKILL_BODY_MAX_LINES = 500

SKILL_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SKILL_DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SKILL_SOURCE = "apigateway"
PLATFORM_SKILL_AUTHOR = "apigateway"
SKILL_FRONTMATTER_KEYS = ("name", "description", "display_name", "display_name_en", "metadata")
SKILL_FRONTMATTER_METADATA_KEYS = ("type", "version", "author", "datetime", "source")

SKILL_FILE_NAME = "SKILL.md"
SKILL_REFERENCE_FILE_NAMES = ("how-to-call-apis.md", "permissions.md")

SKILL_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "skill"
SKILL_TEMPLATES_DIR = SKILL_DATA_DIR / "templates"
SKILL_REFERENCES_DIR = SKILL_DATA_DIR / "references"
SKILL_DECLARATIONS_DIR = SKILL_DATA_DIR / "declarations"
SKILL_RESOURCES_DIR = SKILL_DATA_DIR / "resources"
SKILL_BODY_TEMPLATE_NAME = "SKILL.md.j2"


class SkillReferencePlaceholderEnum(StructuredEnum):
    """references 里的占位符，写成 `{{ name }}`，打包时按部署环境用字符串替换填充"""

    GATEWAY_URL_TEMPLATE = EnumField("gateway_url_template", label="网关访问地址模板")
    EXAMPLE_URL = EnumField("example_url", label="curl 示例地址")
    DEVELOPER_CENTER_URL = EnumField("developer_center_url", label="开发者中心地址")


class SkillSyncStatusEnum(StructuredEnum):
    """内置 Skill 单条注入的结果"""

    CREATED = EnumField("created", label="新建")
    NEW_VERSION = EnumField("new_version", label="新版本")
    SKIPPED_SAME_VERSION = EnumField("skipped_same_version", label="跳过（同版本）")
    SKIPPED_MISSING_RESOURCES = EnumField("skipped_missing_resources", label="跳过（资源缺失）")
    REJECTED = EnumField("rejected", label="拒绝")
    FAILED = EnumField("failed", label="失败")
