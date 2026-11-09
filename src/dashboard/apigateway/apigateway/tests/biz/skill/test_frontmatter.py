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
import datetime

import pytest
import yaml

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.biz.skill import (
    PLATFORM_SKILL_AUTHOR,
    SKILL_SOURCE,
    format_skill_datetime,
    parse_declaration,
    parse_frontmatter,
    render_frontmatter,
    validate_skill_datetime,
)
from apigateway.tests.biz.skill.conftest import EXPECTED_DIR, GOLDEN_NAMES, load_declaration_data

pytestmark = pytest.mark.no_meta_schema

# 2026-10-29T10:00:00Z
PUBLISHED_AT = datetime.datetime(2026, 10, 29, 18, 0, 0, 123456, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))


def _render(name="demo", description="一段说明", **kwargs) -> str:
    params = {
        "display_name": "示例",
        "display_name_en": "Demo",
        "type": SkillTypeEnum.PLATFORM.value,
        "version": "1.0.0",
        "author": PLATFORM_SKILL_AUTHOR,
        "source": SKILL_SOURCE,
        "published_at": PUBLISHED_AT,
    }
    params.update(kwargs)
    return render_frontmatter(name, description, **params)


class TestSkillDatetime:
    def test_format(self):
        assert format_skill_datetime(PUBLISHED_AT) == "2026-10-29T10:00:00Z"

    def test_format_requires_timezone(self):
        with pytest.raises(ValueError):
            format_skill_datetime(datetime.datetime(2026, 10, 29))

    @pytest.mark.parametrize(
        "value", ["2026-10-29T10:00:00+08:00", "2026-10-29 10:00:00Z", "2026-13-01T00:00:00Z", 1, None]
    )
    def test_validate_invalid(self, value):
        with pytest.raises(ValueError):
            validate_skill_datetime(value)

    def test_validate_valid(self):
        validate_skill_datetime("2026-10-29T10:00:00Z")


class TestRenderFrontmatter:
    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_golden(self, name):
        declaration = parse_declaration(load_declaration_data(name))

        text = _render(
            declaration.name,
            declaration.description,
            display_name=declaration.display_name,
            display_name_en=declaration.display_name_en,
            version=declaration.version,
        )

        assert text == (EXPECTED_DIR / f"{name}.frontmatter.md").read_text(encoding="utf-8")

    def test_top_level_keys_in_order(self):
        data = yaml.safe_load(_render().strip("-\n"))

        assert tuple(data) == ("name", "description", "display_name", "display_name_en", "metadata")

    @pytest.mark.parametrize("display_name_en", [None, ""])
    def test_empty_display_name_en(self, display_name_en):
        text = _render(display_name_en=display_name_en)

        assert 'display_name_en: ""\n' in text
        assert yaml.safe_load(text.strip("-\n"))["display_name_en"] == ""

    @pytest.mark.parametrize("display_name", ["含冒号: 的展示名", "true", "123"])
    def test_display_name_round_trip(self, display_name):
        data = yaml.safe_load(_render(display_name=display_name).strip("-\n"))

        assert data["display_name"] == display_name

    @pytest.mark.parametrize(
        "description",
        ["含冒号: 的说明", "- 以短横线开头", "带 #注释 的说明", "'引号开头", "true", "123", "null", "多行\n说明"],
    )
    def test_description_round_trip(self, description):
        data = yaml.safe_load(_render(description=description).strip("-\n"))

        assert data["description"] == description

    def test_metadata_values_are_quoted(self):
        text = _render(version="1.0")

        assert '  version: "1.0"' in text
        assert yaml.safe_load(text.strip("-\n"))["metadata"]["version"] == "1.0"


class TestParseFrontmatter:
    def test_round_trip(self):
        text = _render() + "\n# 正文\n"

        parsed = parse_frontmatter(
            text,
            expected_name="demo",
            expected_description="一段说明",
            expected_display_name="示例",
            expected_display_name_en="Demo",
            expected_type="platform",
        )

        assert parsed.errors == []
        assert parsed.body == "# 正文\n"
        assert parsed.data["metadata"]["datetime"] == "2026-10-29T10:00:00Z"

    def test_no_frontmatter(self):
        assert parse_frontmatter("# 正文\n").errors == ["SKILL.md 应以 --- 包围的 frontmatter 开头"]

    def test_empty_display_name_en(self):
        parsed = parse_frontmatter(_render(display_name_en=None), expected_display_name_en="")

        assert parsed.errors == []
        assert parsed.data["display_name_en"] == ""

    @pytest.mark.parametrize(
        "replace, expected",
        [
            (("name: demo", "name: Demo_1"), "frontmatter.name"),
            (('  version: "1.0.0"', "  version: 1.0"), "frontmatter.metadata.version 应为带引号的字符串"),
            (('  type: "platform"', '  type: "unknown"'), "frontmatter.metadata.type 不合法"),
            (('  author: "apigateway"', '  author: ""'), "frontmatter.metadata.author 不能为空"),
            (('  source: "apigateway"', '  source: "other"'), "frontmatter.metadata.source"),
            (('  datetime: "2026-10-29T10:00:00Z"', '  datetime: "2026-10-29"'), "datetime"),
            (("metadata:", "extra: 1\nmetadata:"), "frontmatter 有规范外的键：extra"),
            (("display_name: 示例\n", ""), "frontmatter 缺少 display_name"),
            (("display_name_en: Demo\n", ""), "frontmatter 缺少 display_name_en"),
            (("display_name: 示例", 'display_name: ""'), "frontmatter.display_name 不能为空"),
            (("display_name: 示例", "display_name: 1"), "frontmatter.display_name 应为字符串"),
            (("display_name_en: Demo", "display_name_en: null"), "frontmatter.display_name_en 应为字符串"),
            (
                ("display_name: 示例\ndisplay_name_en: Demo", "display_name_en: Demo\ndisplay_name: 示例"),
                "frontmatter 的键应依次为 name, description, display_name, display_name_en, metadata",
            ),
            (('  source: "apigateway"\n', ""), "frontmatter.metadata 缺少 source"),
            (
                ('  version: "1.0.0"\n  author: "apigateway"', '  author: "apigateway"\n  version: "1.0.0"'),
                "frontmatter.metadata 的键应依次为 type, version, author, datetime, source",
            ),
        ],
    )
    def test_invalid(self, replace, expected):
        text = _render().replace(*replace)

        errors = parse_frontmatter(text).errors

        assert any(expected in error for error in errors), errors

    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            ({"expected_name": "other"}, "frontmatter.name 与声明不一致"),
            ({"expected_description": "other"}, "frontmatter.description 与声明不一致"),
            ({"expected_display_name": "其他"}, "frontmatter.display_name 与声明不一致"),
            ({"expected_display_name_en": ""}, "frontmatter.display_name_en 与声明不一致"),
            ({"expected_type": "gateway"}, "frontmatter.metadata.type 应为 gateway"),
        ],
    )
    def test_expected_values(self, kwargs, expected):
        errors = parse_frontmatter(_render(), **kwargs).errors

        assert any(expected in error for error in errors), errors
