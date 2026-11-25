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
from apigateway.biz.skill.constants import PLATFORM_SKILL_AUTHOR, SKILL_SOURCE
from apigateway.biz.skill.frontmatter import format_skill_datetime, render_frontmatter

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


class TestRenderFrontmatter:
    def test_keys_in_order(self):
        data = yaml.safe_load(_render().strip("-\n"))

        assert tuple(data) == ("name", "description", "display_name", "display_name_en", "metadata")
        assert tuple(data["metadata"]) == ("type", "version", "author", "datetime", "source")
        assert data["metadata"]["datetime"] == "2026-10-29T10:00:00Z"

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
