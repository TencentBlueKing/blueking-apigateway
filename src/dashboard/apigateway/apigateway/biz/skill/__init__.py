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

from .constants import (
    PLATFORM_SKILL_AUTHOR,
    SKILL_DATETIME_FORMAT,
    SKILL_DECLARATIONS_DIR,
    SKILL_FILE_NAME,
    SKILL_RESOURCES_DIR,
    SKILL_SOURCE,
    SkillReferencePlaceholderEnum,
    SkillSyncStatusEnum,
)
from .declaration import SkillDeclaration, SkillDeclarationError, normalize_tag_name, parse_declaration
from .frontmatter import (
    ParsedFrontmatter,
    format_skill_datetime,
    parse_frontmatter,
    render_frontmatter,
    validate_skill_datetime,
)
from .package import build_skill_files, load_references
from .patch_snapshot import SkillSnapshotError
from .renderer import RenderResult, SkillRenderError, render_skill_body
from .resource_definition import (
    ResourceDefinition,
    ResourceParam,
    ResourceProvider,
    ResponseField,
    StaticResourceProvider,
)
from .resource_loader import ReleasedResourceProvider
from .syncer import SkillSyncResult, get_changed_metadata_ids, sync_platform_skill, sync_platform_skills
from .validator import GatewayRule, MissingResource, ValidationResult, validate_declaration
from .writer import SavedSkillVersion, SkillVersionExistsError, save_skill_version

__all__ = [
    # constant
    "PLATFORM_SKILL_AUTHOR",
    "SKILL_DATETIME_FORMAT",
    "SKILL_DECLARATIONS_DIR",
    "SKILL_FILE_NAME",
    "SKILL_RESOURCES_DIR",
    "SKILL_SOURCE",
    # Enum
    "SkillReferencePlaceholderEnum",
    "SkillSyncStatusEnum",
    # class
    "MissingResource",
    "ParsedFrontmatter",
    "ReleasedResourceProvider",
    "RenderResult",
    "ResourceDefinition",
    "ResourceParam",
    "ResourceProvider",
    "ResponseField",
    "SavedSkillVersion",
    "SkillDeclaration",
    "SkillDeclarationError",
    "SkillRenderError",
    "SkillSnapshotError",
    "SkillSyncResult",
    "SkillVersionExistsError",
    "StaticResourceProvider",
    "ValidationResult",
    # functions
    "build_skill_files",
    "format_skill_datetime",
    "get_changed_metadata_ids",
    "load_references",
    "normalize_tag_name",
    "parse_declaration",
    "parse_frontmatter",
    "render_frontmatter",
    "render_skill_body",
    "save_skill_version",
    "sync_platform_skill",
    "sync_platform_skills",
    "validate_declaration",
    "validate_skill_datetime",
    # others
    "GatewayRule",
]
