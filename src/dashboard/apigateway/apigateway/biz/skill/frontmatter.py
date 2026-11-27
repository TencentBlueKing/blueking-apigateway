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
"""SKILL.md frontmatter 的生成。

以 Agent Skills 规范为基础：顶层依次只有 name、description、display_name、display_name_en、metadata，
display_name_en 为空时写 ""；metadata 依次只有 type、version、author、datetime、source，值都是带引号的字符串。
打包下载时按库里的数据生成；网关 Skill 上传不读包里的 SKILL.md。
"""

import datetime
from typing import Optional

import yaml

from .constants import SKILL_DATETIME_FORMAT

FRONTMATTER_DELIMITER = "---"


class _QuotedStr(str):
    """输出成双引号字符串的值"""


class _FrontmatterDumper(yaml.SafeDumper):
    """frontmatter 的输出格式：_QuotedStr 带双引号，其他字符串同 SafeDumper，必要时才加引号"""


def _represent_quoted(dumper: yaml.SafeDumper, data: _QuotedStr) -> yaml.ScalarNode:
    """_QuotedStr 输出成双引号字符串

    例如：_QuotedStr("1.0") -> "\\"1.0\\""；_QuotedStr("") -> "\\"\\""
    """
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


_FrontmatterDumper.add_representer(_QuotedStr, _represent_quoted)


def format_skill_datetime(value: datetime.datetime) -> str:
    """带时区的时间 -> RFC 3339 UTC 秒精度字符串

    例如：
        2026-10-29 18:00:00.123+08:00 -> "2026-10-29T10:00:00Z"
    """
    return value.astimezone(datetime.timezone.utc).replace(microsecond=0).strftime(SKILL_DATETIME_FORMAT)


def render_frontmatter(
    name: str,
    description: str,
    display_name: str,
    display_name_en: Optional[str],
    type: str,
    version: str,
    author: str,
    source: str,
    published_at: datetime.datetime,
) -> str:
    """生成以 --- 开头和结尾的 frontmatter，末尾带换行；metadata 的值都写成带引号的字符串

    例如：name="demo"、display_name_en=None、published_at 为北京时间 18:00 ->
        "---\\nname: demo\\n...\\ndisplay_name_en: \\"\\"\\nmetadata:\\n  type: \\"gateway\\"\\n...
        \\n  datetime: \\"2026-10-29T10:00:00Z\\"\\n...\\n---\\n"
    """
    data = {
        "name": name,
        "description": description,
        "display_name": display_name,
        "display_name_en": display_name_en or _QuotedStr(),
        "metadata": {
            "type": _QuotedStr(type),
            "version": _QuotedStr(version),
            "author": _QuotedStr(author),
            "datetime": _QuotedStr(format_skill_datetime(published_at)),
            "source": _QuotedStr(source),
        },
    }
    # 不按宽度折行，长描述保持在一行
    text = yaml.dump(data, Dumper=_FrontmatterDumper, allow_unicode=True, sort_keys=False, width=float("inf"))
    return f"{FRONTMATTER_DELIMITER}\n{text}{FRONTMATTER_DELIMITER}\n"
