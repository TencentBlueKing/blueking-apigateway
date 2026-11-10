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
编排的骨架同 GitHub Actions 复合 Action：inputs / outputs / steps，每步 id、name、uses、if、with；
if 和步骤 description 是自然语言，不解析。需要对照资源定义或编排前后关系的规则在 validator.py。
"""

import re
from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    ValidationError,
    field_validator,
)

from apigateway.apps.skill.constants import (
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_DISPLAY_NAME_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    SKILL_TAG_NAME_MAX_LENGTH,
    SKILL_VERSION_MAX_LENGTH,
)
from apigateway.common.constants import GATEWAY_NAME_PATTERN, SEMVER_PATTERN
from apigateway.core.constants import RESOURCE_NAME_PATTERN, STAGE_NAME_PATTERN

from .constants import (
    SKILL_DISPLAY_NAME_EN_PATTERN,
    SKILL_DISPLAY_NAME_PATTERN,
    SKILL_NAME_PATTERN,
    SKILL_STEP_NAME_PATTERN,
)
from .refs import INPUT_NAME, parse_ref

_ERROR_MESSAGES = {
    "extra_forbidden": "未知字段",
    "missing": "缺少必填字段",
    "string_type": "应为字符串",
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


_USES_PATTERN = re.compile(r"^([^/@]+)/([^/@]+)@([^/@]+)$")
_INPUT_NAME_PATTERN = re.compile(rf"^{INPUT_NAME}$")


def _check_ref(value: Any) -> Any:
    parse_ref(value)
    return value


ParamValue = Annotated[Any, AfterValidator(_check_ref)]


class _DeclarationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SkillInput(_DeclarationModel):
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
    type: StrictStr
    description: StrictStr
    value: StrictStr

    @field_validator("value")
    @classmethod
    def _check_value(cls, value: str) -> str:
        if parse_ref(value).kind == "value":
            raise ValueError("应为 ${{ inputs.<输入名> }} 或 ${{ steps.<步骤 id>.outputs.<字段路径> }}")
        return value


def split_uses(uses: str) -> Tuple[str, str, str]:
    """`<网关>/<资源>@<环境>` -> (gateway, stage, resource)；不合规时抛 ValueError"""
    match = _USES_PATTERN.match(uses)
    if not match:
        raise ValueError(f"应为 <网关>/<资源>@<环境>：{uses}")
    gateway, resource, stage = match.groups()
    if not GATEWAY_NAME_PATTERN.fullmatch(gateway):
        raise ValueError(f"网关名不合规：{gateway}")
    if not RESOURCE_NAME_PATTERN.fullmatch(resource):
        raise ValueError(f"资源名不合规：{resource}")
    if not STAGE_NAME_PATTERN.fullmatch(stage):
        raise ValueError(f"环境名不合规：{stage}")
    return gateway, stage, resource


class SkillStep(_DeclarationModel):
    """一步调用一个接口；if 不成立时跳过本步，轮询、逐个调用等写在 description 里"""

    id: StrictStr
    name: Optional[StrictStr] = None
    uses: StrictStr
    if_: Optional[StrictStr] = Field(default=None, alias="if")
    description: StrictStr
    with_: Dict[StrictStr, ParamValue] = Field(default_factory=dict, alias="with")

    @field_validator("id")
    @classmethod
    def _check_id(cls, value: str) -> str:
        if not SKILL_STEP_NAME_PATTERN.fullmatch(value):
            raise ValueError(f"步骤 id 不合规：{value}")
        return value

    @field_validator("uses")
    @classmethod
    def _check_uses(cls, value: str) -> str:
        split_uses(value)
        return value

    @field_validator("name", "if_", "description")
    @classmethod
    def _check_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("为空")
        return value

    @property
    def key(self) -> Tuple[str, str, str]:
        return split_uses(self.uses)

    @property
    def gateway(self) -> str:
        return self.key[0]

    @property
    def stage(self) -> str:
        return self.key[1]

    @property
    def resource(self) -> str:
        return self.key[2]


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
    inputs: Dict[StrictStr, SkillInput]
    outputs: Dict[StrictStr, SkillOutput]
    steps: List[SkillStep]
    guide: SkillGuide

    @field_validator("inputs")
    @classmethod
    def _check_input_names(cls, value: Dict[str, SkillInput]) -> Dict[str, SkillInput]:
        invalid = [name for name in value if not _INPUT_NAME_PATTERN.fullmatch(name)]
        if invalid:
            raise ValueError(f"输入名不合规：{'、'.join(invalid)}")
        return value

    @field_validator("steps")
    @classmethod
    def _check_step_ids(cls, value: List[SkillStep]) -> List[SkillStep]:
        ids = [step.id for step in value]
        duplicated = sorted({step_id for step_id in ids if ids.count(step_id) > 1})
        if duplicated:
            raise ValueError(f"步骤 id 重复：{'、'.join(duplicated)}")
        return value

    def get_input(self, name: str) -> Optional[SkillInput]:
        return self.inputs.get(name)

    def is_omittable_input_ref(self, value: Any) -> bool:
        parsed = parse_ref(value)
        if parsed.kind != "input":
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
        if len(value) > SKILL_NAME_MAX_LENGTH or not SKILL_NAME_PATTERN.fullmatch(value):
            raise ValueError(f"不合规：{value}")
        return value

    @field_validator("display_name")
    @classmethod
    def _check_display_name(cls, value: str) -> str:
        if not (1 <= len(value) <= SKILL_DISPLAY_NAME_MAX_LENGTH and SKILL_DISPLAY_NAME_PATTERN.fullmatch(value)):
            raise ValueError(f"不合规：{value}")
        return value

    @field_validator("display_name_en")
    @classmethod
    def _check_display_name_en(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not (1 <= len(value) <= SKILL_DISPLAY_NAME_MAX_LENGTH and SKILL_DISPLAY_NAME_EN_PATTERN.fullmatch(value)):
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
        if len(value) > SKILL_VERSION_MAX_LENGTH or not SEMVER_PATTERN.fullmatch(value):
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
