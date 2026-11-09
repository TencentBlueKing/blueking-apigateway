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
"""Skill 文件包：SKILL.md（frontmatter + 正文）和 references/ 下的公共说明文件"""

from typing import Dict

from .constants import SKILL_FILE_NAME, SKILL_REFERENCE_FILE_NAMES, SKILL_REFERENCES_DIR


def load_references() -> Dict[str, str]:
    """包内相对路径 -> 带占位符的 references 模板，占位符由打包方按部署环境填充"""
    references = {}
    for name in SKILL_REFERENCE_FILE_NAMES:
        text = (SKILL_REFERENCES_DIR / name).read_text(encoding="utf-8")
        references[f"references/{name}"] = text if text.endswith("\n") else text + "\n"
    return references


def build_skill_files(frontmatter: str, body: str, references: Dict[str, str]) -> Dict[str, str]:
    """包内相对路径 -> 文件内容；frontmatter 由 render_frontmatter 生成，references 传入填充后的内容"""
    files = {SKILL_FILE_NAME: f"{frontmatter}\n{body}"}
    files.update(references)
    return files
