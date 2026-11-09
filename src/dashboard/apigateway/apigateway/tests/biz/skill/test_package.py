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

import pytest

from apigateway.biz.skill import SkillReferencePlaceholderEnum, build_skill_files, load_references, parse_frontmatter

pytestmark = pytest.mark.no_meta_schema

PLACEHOLDER_PATTERN = re.compile(r"{{\s*(\w+)\s*}}")


def test_load_references():
    references = load_references()

    assert sorted(references) == ["references/how-to-call-apis.md", "references/permissions.md"]
    placeholders = {name for text in references.values() for name in PLACEHOLDER_PATTERN.findall(text)}
    assert placeholders == set(SkillReferencePlaceholderEnum.get_values())
    assert not any(re.search(r"woa\.com|bk-dev", text) for text in references.values())


def test_build_skill_files():
    frontmatter = (
        "---\nname: demo\ndescription: 说明\ndisplay_name: 示例\ndisplay_name_en: Demo\nmetadata:\n"
        '  type: "platform"\n  version: "1.0.0"\n  author: "apigateway"\n'
        '  datetime: "2026-10-29T10:00:00Z"\n  source: "apigateway"\n---\n'
    )

    files = build_skill_files(frontmatter, "# 正文\n", {"references/a.md": "a\n"})

    assert files == {"SKILL.md": frontmatter + "\n# 正文\n", "references/a.md": "a\n"}
    parsed = parse_frontmatter(files["SKILL.md"])
    assert parsed.errors == []
    assert parsed.body == "# 正文\n"
