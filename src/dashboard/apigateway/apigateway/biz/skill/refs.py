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
"""编排里的取值引用，写法同 GitHub Actions 的 `${{ }}`。

- `${{ inputs.<输入名> }}`：来自输入；
- `${{ steps.<步骤 id>.outputs.<字段路径> }}`：来自之前某一步调用的响应体；
- 其他值是固定值，按 JSON 原样传。

`${{ }}` 必须占满整个字符串，也不能写在对象、数组固定值的里面。
"""

import re
from dataclasses import dataclass
from typing import Any

_EXPR_PATTERN = re.compile(r"^\$\{\{\s*(.*?)\s*\}\}$")
INPUT_NAME = r"[A-Za-z_][A-Za-z0-9_-]*"
_FIELD_NAME = r"[A-Za-z_][A-Za-z0-9_-]*(?:\[\d*\])*"
_FIELD_PATH = rf"{_FIELD_NAME}(?:\.{_FIELD_NAME})*"
_INPUT_REF_PATTERN = re.compile(rf"^inputs\.({INPUT_NAME})$")
_STEP_REF_PATTERN = re.compile(rf"^steps\.([a-z0-9-]+)\.outputs\.({_FIELD_PATH})$")
_EXPR_MARK = "${{"


@dataclass(frozen=True)
class ParsedRef:
    """kind: input / step / value"""

    kind: str
    name: str = ""
    step: str = ""
    path: str = ""
    value: Any = None


def parse_ref(value: Any) -> ParsedRef:
    """解析取值；`${{ }}` 写法不对时抛 ValueError"""
    if isinstance(value, str) and _EXPR_MARK in value:
        match = _EXPR_PATTERN.match(value)
        if not match or _EXPR_MARK in match.group(1) or "}}" in match.group(1):
            raise ValueError(f"`${{{{ }}}}` 必须占满整个字符串，不能和其他文字拼接：{value}")
        expr = match.group(1)
        input_match = _INPUT_REF_PATTERN.match(expr)
        if input_match:
            return ParsedRef(kind="input", name=input_match.group(1))
        step_match = _STEP_REF_PATTERN.match(expr)
        if step_match:
            return ParsedRef(kind="step", step=step_match.group(1), path=step_match.group(2))
        raise ValueError(f"只能引用 inputs.<输入名> 或 steps.<步骤 id>.outputs.<字段路径>：{value}")
    if _contains_expr(value):
        raise ValueError(f"`${{{{ }}}}` 只能作为整个取值，不能写在对象或数组里：{value}")
    return ParsedRef(kind="value", value=value)


def is_ref(value: Any) -> bool:
    return parse_ref(value).kind != "value"


def norm_path(path: str) -> str:
    """把 [0]、[n] 统一成资源定义里的 []"""
    return re.sub(r"\[\d*\]", "[]", path)


def _contains_expr(value: Any) -> bool:
    if isinstance(value, str):
        return _EXPR_MARK in value
    if isinstance(value, dict):
        return any(_contains_expr(key) or _contains_expr(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_expr(item) for item in value)
    return False
