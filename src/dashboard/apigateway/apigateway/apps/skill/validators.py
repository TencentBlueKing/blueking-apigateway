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
"""Skill 字段校验，供注入声明校验和管理接口共用"""

import re
from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apigateway.common.constants import SEMVER_PATTERN

from .constants import (
    SKILL_DATETIME_FORMAT,
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_DISPLAY_NAME_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    SKILL_TAG_NAME_MAX_LENGTH,
    SKILL_VERSION_MAX_LENGTH,
)

# Agent Skills 规范名：小写字母、数字、连字符；不以连字符开头或结尾，不含连续连字符
SKILL_NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# 字母（含中文）、数字、连字符，词之间用单个空格分隔；[^\W_] 为去掉下划线的 \w
_SKILL_DISPLAY_NAME_WORD = r"(?:[^\W_]|-)+"
SKILL_DISPLAY_NAME_PATTERN = re.compile(rf"{_SKILL_DISPLAY_NAME_WORD}(?: {_SKILL_DISPLAY_NAME_WORD})*")

_SKILL_DISPLAY_NAME_EN_WORD = r"[A-Za-z0-9-]+"
SKILL_DISPLAY_NAME_EN_PATTERN = re.compile(rf"{_SKILL_DISPLAY_NAME_EN_WORD}(?: {_SKILL_DISPLAY_NAME_EN_WORD})*")

SKILL_DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

# 表按 utf8mb3 处理，不能存码点大于 U+FFFF 的字符（如 emoji）
_MAX_BMP_CODE_POINT = 0xFFFF


def _validate_no_4byte_chars(value: str) -> None:
    if any(ord(char) > _MAX_BMP_CODE_POINT for char in value):
        raise ValidationError(_("4-byte characters (such as emoji) are not supported."), code="invalid_char")


def _validate_length(value: str, max_length: int, min_length: int = 1) -> None:
    if len(value) < min_length:
        raise ValidationError(
            _("Ensure this value has at least %(min_length)s characters."),
            code="min_length",
            params={"min_length": min_length},
        )
    if len(value) > max_length:
        raise ValidationError(
            _("Ensure this value has at most %(max_length)s characters."),
            code="max_length",
            params={"max_length": max_length},
        )


def validate_skill_name(value: str) -> None:
    _validate_length(value, SKILL_NAME_MAX_LENGTH)
    if not SKILL_NAME_PATTERN.fullmatch(value):
        raise ValidationError(
            _("Use lowercase letters, digits and single hyphens, not starting or ending with a hyphen."),
            code="invalid",
        )


def validate_skill_display_name(value: str) -> None:
    _validate_no_4byte_chars(value)
    _validate_length(value, SKILL_DISPLAY_NAME_MAX_LENGTH)
    if not SKILL_DISPLAY_NAME_PATTERN.fullmatch(value):
        raise ValidationError(
            _("Use letters, digits, hyphens and single spaces, not starting or ending with a space."),
            code="invalid",
        )


def validate_skill_display_name_en(value: str) -> None:
    _validate_length(value, SKILL_DISPLAY_NAME_MAX_LENGTH)
    if not SKILL_DISPLAY_NAME_EN_PATTERN.fullmatch(value):
        raise ValidationError(
            _("Use English letters, digits, hyphens and single spaces, not starting or ending with a space."),
            code="invalid",
        )


def validate_skill_description(value: str) -> None:
    _validate_no_4byte_chars(value)
    _validate_length(value, SKILL_DESCRIPTION_MAX_LENGTH)


def validate_skill_changelog(value: str) -> None:
    _validate_no_4byte_chars(value)


def validate_skill_version(value: str) -> str:
    """转为小写后校验；写入和查询都使用返回值，大小写不同视为同一版本"""
    value = value.lower()
    _validate_length(value, SKILL_VERSION_MAX_LENGTH)
    # SEMVER_PATTERN 的 \d 会匹配非 ASCII 数字（如 ١），共享正则不改，在这里排除
    if not value.isascii() or not SEMVER_PATTERN.fullmatch(value):
        raise ValidationError(_("Enter a valid semantic version, such as 1.0.0."), code="invalid")
    return value


def validate_skill_datetime(value: str) -> None:
    if not SKILL_DATETIME_PATTERN.fullmatch(value):
        raise ValidationError(_("Enter a valid UTC datetime, such as 2026-11-06T08:09:00Z."), code="invalid")
    try:
        datetime.strptime(value, SKILL_DATETIME_FORMAT)
    except ValueError:
        raise ValidationError(_("Enter a valid UTC datetime, such as 2026-11-06T08:09:00Z."), code="invalid") from None


def normalize_tag_name(value: str) -> str:
    """去除首尾空白并转为小写后校验，返回规范化后的标签名"""
    value = value.strip().lower()
    _validate_no_4byte_chars(value)
    _validate_length(value, SKILL_TAG_NAME_MAX_LENGTH)
    return value
