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
"""Skill 声明的结构与字段规则。

声明由人工编写（内置 Skill）或随上传包提供（网关 Skill），结构不对时报带路径的 error。
需要对照资源定义或编排前后关系的规则在 validator.py。
"""

from typing import Annotated, Any, Dict, Iterator, List, Optional, Tuple, Union

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
    field_validator,
    model_validator,
)

from apigateway.apps.skill.constants import (
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_DISPLAY_NAME_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    SKILL_TAG_NAME_MAX_LENGTH,
    SKILL_VERSION_MAX_LENGTH,
)
from apigateway.common.constants import SEMVER_PATTERN

from .constants import (
    SKILL_DISPLAY_NAME_EN_PATTERN,
    SKILL_DISPLAY_NAME_PATTERN,
    SKILL_NAME_PATTERN,
    SKILL_STEP_NAME_PATTERN,
)
from .refs import ParsedRef, parse_poll_expr, parse_ref, ref_text, ref_where

_ERROR_MESSAGES = {
    "extra_forbidden": "未知字段",
    "missing": "缺少必填字段",
    "string_type": "应为字符串",
    "int_type": "应为整数",
    "bool_type": "应为布尔值",
    "list_type": "应为数组",
    "dict_type": "应为对象",
    "model_type": "应为对象",
    "model_attributes_type": "应为对象",
}


class SkillDeclarationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def _check_ref(value: Any) -> Any:
    parse_ref(value)
    return value


ParamRef = Annotated[Any, AfterValidator(_check_ref)]


class _DeclarationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SkillInput(_DeclarationModel):
    name: StrictStr
    type: StrictStr
    required: StrictBool
    description: StrictStr
    example: Any
    default: Any = None

    @property
    def has_default(self) -> bool:
        return "default" in self.model_fields_set

    @property
    def omit_if_unset(self) -> bool:
        """选填且没有默认值：用户没给时整个参数不传"""
        return not self.required and not self.has_default


class SkillOutput(_DeclarationModel):
    name: StrictStr
    type: StrictStr
    description: StrictStr
    from_: StrictStr = Field(alias="from")

    @field_validator("from_")
    @classmethod
    def _check_from(cls, value: str) -> str:
        return _check_ref(value)


class SkillForEach(_DeclarationModel):
    from_: StrictStr = Field(alias="from")
    where: Optional[StrictStr] = None

    @field_validator("from_")
    @classmethod
    def _check_from(cls, value: str) -> str:
        if parse_ref(value).kind != "call":
            raise ValueError("必须引用之前调用的响应数组")
        return value


class SkillPoll(_DeclarationModel):
    """until、stop_when 是 `<响应体字段路径> <==|!=|in|not in> <JSON 值>` 表达式；
    stop_when 的元素也可以写 {expr, times}，表示连续成立 times 次才停止
    """

    interval: StrictInt
    max: StrictInt
    until: StrictStr
    stop_when: List[Any] = Field(default_factory=list)

    @field_validator("interval", "max")
    @classmethod
    def _check_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("应为正整数")
        return value

    @field_validator("until")
    @classmethod
    def _check_until(cls, value: str) -> str:
        _check_poll_expr(value)
        return value

    @field_validator("stop_when")
    @classmethod
    def _check_stop_when(cls, value: List[Any]) -> List[Any]:
        for item in value:
            if isinstance(item, str):
                _check_poll_expr(item)
                continue
            if not (
                isinstance(item, dict)
                and set(item) == {"expr", "times"}
                and isinstance(item["expr"], str)
                and isinstance(item["times"], int)
                and not isinstance(item["times"], bool)
                and item["times"] > 0
            ):
                raise ValueError("每项应为表达式，或 {expr, times}（连续成立 times 次才停止）")
            _check_poll_expr(item["expr"])
        return value

    @property
    def stop_conditions(self) -> List[Tuple[str, int]]:
        """stop_when 的每一项规整成 (表达式, 连续成立次数)"""
        return [(item, 1) if isinstance(item, str) else (item["expr"], item["times"]) for item in self.stop_when]

    @property
    def exprs(self) -> List[str]:
        return [self.until] + [expr for expr, _ in self.stop_conditions]


def _check_poll_expr(expr: str) -> None:
    path = parse_poll_expr(expr)[0]
    if "[" in path:
        raise ValueError(f"表达式只支持对象字段路径，不支持数组：{expr}")


class SkillCall(_DeclarationModel):
    gateway: StrictStr
    stage: StrictStr
    resource: StrictStr
    params: Dict[StrictStr, ParamRef]
    for_each: Optional[SkillForEach] = None
    reads: List[StrictStr] = Field(default_factory=list)
    poll: Optional[SkillPoll] = None

    @model_validator(mode="after")
    def _check_call(self) -> "SkillCall":
        if self.poll and self.for_each:
            raise ValueError("poll 和 for_each 不能同时使用")
        for name, ref in self.params.items():
            if parse_ref(ref).kind == "each" and self.for_each is None:
                raise ValueError(f"params.{name}：只有带 for_each 的调用能用 each.*")
            if ref_where(ref) is not None and "[]" not in (ref_text(ref) or ""):
                raise ValueError(f"params.{name}：where 只能用在取数组元素字段（含 []）的引用上")
        return self

    @property
    def key(self) -> Tuple[str, str, str]:
        return self.gateway, self.stage, self.resource


class SkillStep(_DeclarationModel):
    name: StrictStr
    description: StrictStr
    calls: List[SkillCall]

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if not SKILL_STEP_NAME_PATTERN.match(value):
            raise ValueError(f"步骤名不合规：{value}")
        return value

    @field_validator("calls")
    @classmethod
    def _check_calls(cls, value: List[SkillCall]) -> List[SkillCall]:
        if not value:
            raise ValueError("步骤没有调用")
        return value


class SkillGuide(_DeclarationModel):
    not_for: StrictStr
    constraints: StrictStr
    errors: StrictStr
    example: StrictStr

    @field_validator("not_for", "constraints", "errors", "example")
    @classmethod
    def _check_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("为空（没有内容写「无」）")
        return value


class SkillOrchestration(_DeclarationModel):
    description: StrictStr
    inputs: List[SkillInput]
    outputs: List[SkillOutput]
    steps: List[SkillStep]
    guide: SkillGuide

    @field_validator("steps")
    @classmethod
    def _check_step_names(cls, value: List[SkillStep]) -> List[SkillStep]:
        names = [step.name for step in value]
        duplicated = sorted({name for name in names if names.count(name) > 1})
        if duplicated:
            raise ValueError(f"步骤名重复：{'、'.join(duplicated)}")
        return value

    def iter_calls(self) -> Iterator[Tuple[SkillStep, SkillCall]]:
        for step in self.steps:
            for call in step.calls:
                yield step, call

    def get_input(self, name: str) -> Optional[SkillInput]:
        return next((item for item in self.inputs if item.name == name), None)

    def is_omittable_input_ref(self, ref: Any) -> bool:
        parsed = _safe_parse_ref(ref)
        if parsed is None or parsed.kind != "input":
            return False
        item = self.get_input(parsed.name)
        return bool(item and item.omit_if_unset)


class SkillDeclaration(_DeclarationModel):
    name: StrictStr
    display_name: StrictStr
    display_name_en: Optional[StrictStr] = None
    description: StrictStr
    tags: List[StrictStr]
    version: StrictStr
    changelog: StrictStr = ""
    orchestration: SkillOrchestration

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if len(value) > SKILL_NAME_MAX_LENGTH or not SKILL_NAME_PATTERN.match(value):
            raise ValueError(f"不合规：{value}")
        return value

    @field_validator("display_name")
    @classmethod
    def _check_display_name(cls, value: str) -> str:
        if not (1 <= len(value) <= SKILL_DISPLAY_NAME_MAX_LENGTH and SKILL_DISPLAY_NAME_PATTERN.match(value)):
            raise ValueError(f"不合规：{value}")
        return value

    @field_validator("display_name_en", mode="before")
    @classmethod
    def _check_display_name_en(cls, value: Any) -> Any:
        if not (
            isinstance(value, str)
            and 1 <= len(value) <= SKILL_DISPLAY_NAME_MAX_LENGTH
            and SKILL_DISPLAY_NAME_EN_PATTERN.match(value)
        ):
            raise ValueError(f"不合规：{value}")
        return value

    @field_validator("description")
    @classmethod
    def _check_description(cls, value: str) -> str:
        if not 1 <= len(value) <= SKILL_DESCRIPTION_MAX_LENGTH:
            raise ValueError(f"长度应为 1–{SKILL_DESCRIPTION_MAX_LENGTH}")
        return value

    @field_validator("tags")
    @classmethod
    def _check_tags(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("至少需要一个标签")
        normalized = [normalize_tag_name(tag) for tag in value]
        for tag, name in zip(value, normalized):
            if not 1 <= len(name) <= SKILL_TAG_NAME_MAX_LENGTH:
                raise ValueError(f"标签名长度应为 1–{SKILL_TAG_NAME_MAX_LENGTH}：{tag!r}")
        for index, name in enumerate(normalized):
            if name in normalized[:index]:
                raise ValueError(f"标签规范化后重复：{name}")
        return value

    @field_validator("version")
    @classmethod
    def _check_version(cls, value: str) -> str:
        if len(value) > SKILL_VERSION_MAX_LENGTH or not SEMVER_PATTERN.match(value):
            raise ValueError(f"不是 Semver：{value}")
        return value

    @property
    def normalized_tags(self) -> List[str]:
        return [normalize_tag_name(tag) for tag in self.tags]

    def orchestration_data(self) -> Dict[str, Any]:
        """写入 skill_config / skill_version 的编排内容，与声明里的 orchestration 一致"""
        return self.orchestration.model_dump(mode="json", by_alias=True, exclude_unset=True)


def normalize_tag_name(name: str) -> str:
    return name.strip().lower()


def parse_declaration(data: Union[str, Dict[str, Any]]) -> SkillDeclaration:
    """YAML 文本或 dict -> 声明；不合规时抛 SkillDeclarationError，errors 里每条带字段路径"""
    if isinstance(data, str):
        try:
            data = yaml.safe_load(data)
        except yaml.YAMLError as err:
            raise SkillDeclarationError([f"YAML 解析失败：{' '.join(str(err).split())}"]) from None

    try:
        return SkillDeclaration.model_validate(data)
    except ValidationError as err:
        raise SkillDeclarationError([_format_error(item) for item in err.errors()]) from None


def _format_error(error: Dict[str, Any]) -> str:
    path = _format_loc(error["loc"]) or "声明"
    if error["type"] == "value_error":
        message = str(error["ctx"]["error"])
    else:
        message = _ERROR_MESSAGES.get(error["type"], error["msg"])
    return f"{path}: {message}"


def _format_loc(loc: Tuple[Union[str, int], ...]) -> str:
    text = ""
    for part in loc:
        if isinstance(part, int):
            text += f"[{part}]"
        else:
            text += f".{part}" if text else str(part)
    return text


def _safe_parse_ref(ref: Any) -> Optional[ParsedRef]:
    try:
        return parse_ref(ref)
    except ValueError:
        return None
