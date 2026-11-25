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
import json
import re
from typing import Optional

import yaml

from .constants import SKILL_DATETIME_FORMAT

FRONTMATTER_DELIMITER = "---"
_YAML_PLAIN_UNSAFE_PATTERN = re.compile(r":\s|^[\s\-?:,\[\]{}#&*!|>'\"%@`]|\s#")


def format_skill_datetime(value: datetime.datetime) -> str:
    """带时区的时间 -> RFC 3339 UTC 秒精度字符串；不带时区时抛 ValueError

    例如：
        2026-10-29 18:00:00.123+08:00 -> "2026-10-29T10:00:00Z"
        datetime(2026, 10, 29)（无时区）-> ValueError
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("published_at must be timezone-aware")
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
    metadata = {
        "type": type,
        "version": version,
        "author": author,
        "datetime": format_skill_datetime(published_at),
        "source": source,
    }
    lines = [
        FRONTMATTER_DELIMITER,
        f"name: {name}",
        f"description: {_yaml_scalar(description)}",
        f"display_name: {_yaml_scalar(display_name)}",
        f"display_name_en: {_yaml_scalar(display_name_en or '')}",
        "metadata:",
        *(f"  {key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()),
        FRONTMATTER_DELIMITER,
    ]
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: str) -> str:
    """能作为 YAML 普通标量原样读回时不加引号，否则输出 JSON 字符串（也是合法的 YAML 双引号字符串）

    例如："执行作业方案" -> 执行作业方案；"a: b" -> "\\"a: b\\""；"" -> "\\"\\""；"123" -> "\\"123\\""
    """
    if _YAML_PLAIN_UNSAFE_PATTERN.search(value):
        return json.dumps(value, ensure_ascii=False)
    try:
        if value and yaml.safe_load(f"k: {value}") == {"k": value}:
            return value
    except yaml.YAMLError:
        pass
    return json.dumps(value, ensure_ascii=False)
