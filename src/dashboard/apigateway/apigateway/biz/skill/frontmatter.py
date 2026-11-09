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
"""SKILL.md frontmatter 的生成与解析。

以 Agent Skills 规范为基础：顶层依次只有 name、description、display_name、display_name_en、metadata，
display_name_en 为空时写 ""；metadata 依次只有 type、version、author、datetime、source，值都是带引号的字符串。
内置 Skill、网关 Skill 和 Skill Creator 产物共用这一份规则。
"""

import datetime
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

from apigateway.apps.skill.constants import SkillTypeEnum

from .constants import (
    SKILL_DATETIME_FORMAT,
    SKILL_DATETIME_PATTERN,
    SKILL_FRONTMATTER_KEYS,
    SKILL_FRONTMATTER_METADATA_KEYS,
    SKILL_NAME_PATTERN,
    SKILL_SOURCE,
)

FRONTMATTER_DELIMITER = "---"
_YAML_PLAIN_UNSAFE_PATTERN = re.compile(r":\s|^[\s\-?:,\[\]{}#&*!|>'\"%@`]|\s#")


@dataclass
class ParsedFrontmatter:
    data: Dict[str, Any] = field(default_factory=dict)
    body: str = ""
    errors: List[str] = field(default_factory=list)


def format_skill_datetime(value: datetime.datetime) -> str:
    """带时区的时间 -> RFC 3339 UTC 秒精度，如 2026-10-29T10:00:00Z"""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("published_at 必须带时区")
    return value.astimezone(datetime.timezone.utc).replace(microsecond=0).strftime(SKILL_DATETIME_FORMAT)


def validate_skill_datetime(value: Any) -> None:
    """检查形如 YYYY-MM-DDTHH:MM:SSZ 且是真实日期；不合规时抛 ValueError"""
    if not isinstance(value, str) or not SKILL_DATETIME_PATTERN.match(value):
        raise ValueError(f"datetime 应为 YYYY-MM-DDTHH:MM:SSZ 格式的字符串：{value!r}")
    try:
        datetime.datetime.strptime(value, SKILL_DATETIME_FORMAT)
    except ValueError:
        raise ValueError(f"datetime 不是有效时间：{value}") from None


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
    """返回以 --- 开头和结尾的 frontmatter，末尾带换行"""
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


def parse_frontmatter(
    text: str,
    *,
    expected_name: Optional[str] = None,
    expected_description: Optional[str] = None,
    expected_display_name: Optional[str] = None,
    expected_display_name_en: Optional[str] = None,
    expected_type: Optional[str] = None,
) -> ParsedFrontmatter:
    """解析 SKILL.md，按 metadata 规范校验；body 是 frontmatter 之后的正文（去掉分隔用的空行）

    expected_* 为 None 时不比对；声明没填英文展示名时传 ""。
    """
    result = ParsedFrontmatter()
    lines = text.split("\n")
    if not lines or lines[0] != FRONTMATTER_DELIMITER or FRONTMATTER_DELIMITER not in lines[1:]:
        result.errors.append("SKILL.md 应以 --- 包围的 frontmatter 开头")
        return result

    end = lines.index(FRONTMATTER_DELIMITER, 1)
    result.body = "\n".join(lines[end + 1 :]).lstrip("\n")
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as err:
        result.errors.append(f"frontmatter 不是合法的 YAML：{err}")
        return result
    if not isinstance(data, dict):
        result.errors.append("frontmatter 应为键值对")
        return result

    result.data = data
    result.errors += _check_keys("frontmatter", data, SKILL_FRONTMATTER_KEYS)
    result.errors += _check_top_level(data, expected_name, expected_description)
    result.errors += _check_display_names(data, expected_display_name, expected_display_name_en)

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        result.errors.append("frontmatter.metadata 应为键值对")
        return result
    result.errors += _check_keys("frontmatter.metadata", metadata, SKILL_FRONTMATTER_METADATA_KEYS)
    result.errors += _check_metadata(metadata, expected_type)
    return result


def _check_keys(where: str, data: Dict[str, Any], expected: tuple) -> List[str]:
    errors = [f"{where} 缺少 {key}" for key in expected if key not in data]
    errors += [f"{where} 有规范外的键：{key}" for key in data if key not in expected]
    if not errors and tuple(data) != expected:
        errors.append(f"{where} 的键应依次为 {', '.join(expected)}")
    return errors


def _check_top_level(data: Dict[str, Any], expected_name: Optional[str], expected_description: Optional[str]):
    errors = []
    name, description = data.get("name"), data.get("description")
    if "name" in data:
        if not isinstance(name, str) or not SKILL_NAME_PATTERN.match(name):
            errors.append(f"frontmatter.name 不合规：{name!r}")
        elif expected_name is not None and name != expected_name:
            errors.append(f"frontmatter.name 与声明不一致：{name}")
    if "description" in data:
        if not isinstance(description, str) or not description:
            errors.append("frontmatter.description 应为非空字符串")
        elif expected_description is not None and description != expected_description:
            errors.append("frontmatter.description 与声明不一致")
    return errors


def _check_display_names(
    data: Dict[str, Any], expected_display_name: Optional[str], expected_display_name_en: Optional[str]
) -> List[str]:
    errors = []
    expected = {"display_name": expected_display_name, "display_name_en": expected_display_name_en}
    for key, expected_value in expected.items():
        if key not in data:
            continue
        value = data[key]
        if not isinstance(value, str):
            errors.append(f"frontmatter.{key} 应为字符串：{value!r}")
        elif key == "display_name" and not value:
            errors.append("frontmatter.display_name 不能为空")
        elif expected_value is not None and value != expected_value:
            errors.append(f"frontmatter.{key} 与声明不一致：{value}")
    return errors


def _check_metadata(metadata: Dict[str, Any], expected_type: Optional[str]) -> List[str]:
    errors = [
        f"frontmatter.metadata.{key} 应为带引号的字符串：{metadata[key]!r}"
        for key in SKILL_FRONTMATTER_METADATA_KEYS
        if key in metadata and not isinstance(metadata[key], str)
    ]

    skill_type = metadata.get("type")
    if isinstance(skill_type, str):
        if skill_type not in SkillTypeEnum.get_values():
            errors.append(f"frontmatter.metadata.type 不合法：{skill_type}")
        elif expected_type is not None and skill_type != expected_type:
            errors.append(f"frontmatter.metadata.type 应为 {expected_type}：{skill_type}")
    if isinstance(metadata.get("author"), str) and not metadata["author"]:
        errors.append("frontmatter.metadata.author 不能为空")
    if isinstance(metadata.get("source"), str) and metadata["source"] != SKILL_SOURCE:
        errors.append(f"frontmatter.metadata.source 应为 {SKILL_SOURCE}：{metadata['source']}")
    if isinstance(metadata.get("datetime"), str):
        try:
            validate_skill_datetime(metadata["datetime"])
        except ValueError as err:
            errors.append(f"frontmatter.metadata.{err}")
    return errors


def _yaml_scalar(value: str) -> str:
    """能作为 YAML 普通标量原样读回时不加引号，否则输出 JSON 字符串（也是合法的 YAML 双引号字符串）"""
    if _YAML_PLAIN_UNSAFE_PATTERN.search(value):
        return json.dumps(value, ensure_ascii=False)
    try:
        if yaml.safe_load(f"k: {value}") == {"k": value}:
            return value
    except yaml.YAMLError:
        pass
    return json.dumps(value, ensure_ascii=False)
