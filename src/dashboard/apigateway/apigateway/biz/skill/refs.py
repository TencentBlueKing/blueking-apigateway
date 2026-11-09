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
"""编排里的取值引用与轮询表达式。

引用有四种写法：
- `inputs.<输入名>`：来自输入；
- `<步骤>.<资源>.<字段路径>`：来自之前某次调用的响应体；
- `each.<字段路径>`：带 for_each 的调用里当前元素的字段；
- `{"value": <JSON 值>}` 固定值，或 `{"ref": <上面三种字符串>, "where": <条件>}` 只取满足条件的数组元素。
  `ref` 只能是字符串，不能再套一层对象。
"""

import json
import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

POLL_EXPR_PATTERN = re.compile(r"^\s*([A-Za-z_][\w.\[\]]*)\s+(==|!=|not in|in)\s+(.+?)\s*$")


@dataclass(frozen=True)
class ParsedRef:
    """kind: input / call / each / value"""

    kind: str
    name: str = ""
    step: str = ""
    resource: str = ""
    path: str = ""
    value: Any = None


def parse_ref(ref: Any) -> ParsedRef:
    """解析引用；格式不对时抛 ValueError"""
    if isinstance(ref, dict):
        if set(ref) == {"ref", "where"}:
            if not isinstance(ref["ref"], str):
                raise ValueError(f"ref 应为字符串：{ref}")
            if not isinstance(ref["where"], str) or not ref["where"]:
                raise ValueError(f"where 应为非空字符串：{ref}")
            return parse_ref(ref["ref"])
        if set(ref) != {"value"}:
            raise ValueError(f'引用对象只允许 {{"value": ...}} 或 {{"ref": ..., "where": ...}}：{ref}')
        return ParsedRef(kind="value", value=ref["value"])
    if not isinstance(ref, str):
        # pydantic 校验器只把 ValueError 转成校验错误
        raise ValueError(f"引用必须是字符串或固定值对象：{ref!r}")  # noqa: TRY004
    if ref.startswith("inputs."):
        return ParsedRef(kind="input", name=ref[len("inputs.") :])
    if ref.startswith("each."):
        return ParsedRef(kind="each", path=ref[len("each.") :])
    parts = ref.split(".", 2)
    if len(parts) < 3 or not parts[2]:
        raise ValueError(f"引用格式应为 <step>.<resource>.<字段路径>：{ref}")
    return ParsedRef(kind="call", step=parts[0], resource=parts[1], path=parts[2])


def ref_text(ref: Any) -> Optional[str]:
    """引用的字符串形式；固定值返回 None"""
    if isinstance(ref, dict):
        inner = ref.get("ref")
        return inner if isinstance(inner, str) else None
    return ref


def ref_where(ref: Any) -> Optional[str]:
    if isinstance(ref, dict):
        return ref.get("where")
    return None


def norm_path(path: str) -> str:
    """把 [0]、[n] 统一成资源定义里的 []"""
    return re.sub(r"\[\d*\]", "[]", path)


def parse_poll_expr(expr: str) -> Tuple[str, str, Any]:
    """`<响应体字段路径> <==|!=|in|not in> <JSON 值>` -> (path, op, value)"""
    match = POLL_EXPR_PATTERN.match(expr)
    if not match:
        raise ValueError(f"轮询表达式应为「字段路径 ==|!=|in|not in JSON 值」：{expr}")
    path, op, raw = match.groups()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"轮询表达式右侧应为 JSON 值：{expr}") from None
    if op in ("in", "not in") and not isinstance(value, list):
        raise ValueError(f"{op} 右侧应为 JSON 数组：{expr}")
    return path, op, value


def poll_expr_paths(exprs: List[str]) -> List[str]:
    """表达式在解析声明时已经校验过，这里不再吞掉解析错误"""
    paths: List[str] = []
    for expr in exprs:
        path = parse_poll_expr(expr)[0]
        if path not in paths:
            paths.append(path)
    return paths
