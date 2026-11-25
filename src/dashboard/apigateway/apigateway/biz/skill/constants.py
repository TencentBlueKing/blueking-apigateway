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
from django.utils.translation import gettext_lazy as _

# Agent Skills 规范名：小写字母、数字、单个连字符，1–64，不以连字符开头或结尾；步骤 id 同规则
SKILL_NAME_PATTERN = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

SKILL_BODY_MAX_LINES = 500

SKILL_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SKILL_SOURCE = "apigateway"
PLATFORM_SKILL_AUTHOR = "apigateway"

SKILL_FILE_NAME = "SKILL.md"
SKILL_DECLARATION_FILE_NAME = "declaration.yaml"
SKILL_REFERENCES_PATH = "references"
SKILL_REFERENCE_FILE_NAMES = ("how-to-call-apis.md", "permissions.md")

SKILL_DATA_DIR = Path(settings.SKILL_DATA_DIR)
SKILL_TEMPLATES_DIR = SKILL_DATA_DIR / "templates"
SKILL_DECLARATIONS_DIR = SKILL_DATA_DIR / "declarations"
SKILL_REFERENCES_DIR = SKILL_DATA_DIR / SKILL_REFERENCES_PATH
SKILL_BODY_TEMPLATE_NAME = "SKILL.md.j2"

# 上传的 zip 包大小上限，单位字节
SKILL_PACKAGE_MAX_SIZE = 2 * 1024 * 1024

# 网关 Skill 管理页下载的包带 declaration.yaml，包名加这个后缀
SKILL_DECLARATION_PACKAGE_SUFFIX = "-with-declaration"


class SkillReferencePlaceholderEnum(StructuredEnum):
    """references 里的占位符，写成 `{{ name }}`，打包时按部署环境用字符串替换填充"""

    GATEWAY_URL_TEMPLATE = EnumField("gateway_url_template", label=_("网关访问地址模板"))
    EXAMPLE_URL = EnumField("example_url", label=_("curl 示例地址"))
    DEVELOPER_CENTER_URL = EnumField("developer_center_url", label=_("开发者中心地址"))


class SkillSyncStatusEnum(StructuredEnum):
    """内置 Skill 单条注入的结果"""

    CREATED = EnumField("created", label=_("新建"))
    RELEASED = EnumField("released", label=_("发布"))
    SKIPPED = EnumField("skipped", label=_("跳过"))
