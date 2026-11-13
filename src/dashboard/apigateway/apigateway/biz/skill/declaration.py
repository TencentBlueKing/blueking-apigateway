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
编排的骨架同 GitHub Actions 复合 Action：inputs / outputs / steps，每步 id、name、uses、with；
步骤 description 是自然语言，执行条件、轮询、逐个调用都写在里面，不解析。
需要对照资源定义或编排前后关系的规则在 validator.py。
"""

import datetime
import re
from typing import Annotated, Any, Callable, Dict, List, Optional, Tuple, Union

import yaml
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from apigateway.apps.skill.constants import (
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_DISPLAY_NAME_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    SKILL_TAG_NAME_MAX_LENGTH,
    SKILL_VERSION_MAX_LENGTH,
    SKILL_VERSION_PATTERN,
)
from apigateway.common.constants import GATEWAY_NAME_PATTERN
from apigateway.core.constants import RESOURCE_NAME_PATTERN, STAGE_NAME_PATTERN

from .constants import (
    SKILL_NAME_PATTERN,
    SKILL_STEP_NAME_PATTERN,
)
from .refs import INPUT_NAME, parse_ref

_ERROR_MESSAGES = {
    "extra_forbidden": gettext_lazy("未知字段"),
    "missing": gettext_lazy("缺少必填字段"),
    "string_type": gettext_lazy("应为字符串"),
    "bool_type": gettext_lazy("应为布尔值"),
    "list_type": gettext_lazy("应为数组"),
    "dict_type": gettext_lazy("应为对象"),
    "model_type": gettext_lazy("应为对象"),
    "model_attributes_type": gettext_lazy("应为对象"),
}


class SkillDeclarationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


_USES_PATTERN = re.compile(r"^([^/@]+)/([^/@]+)@([^/@]+)$")
_INPUT_NAME_PATTERN = re.compile(rf"^{INPUT_NAME}$")
_ARRAY_TYPE_PATTERN = re.compile(r"^array<(.+)>$")
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$")

# 类型写法同资源定义（schema_converter.schema_type_text）：基本类型、array<类型>、基本类型|基本类型
_JSON_TYPE_CHECKS: Dict[str, Callable[[Any], bool]] = {
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
    "null": lambda value: value is None,
}


def is_type_text(text: str) -> bool:
    match = _ARRAY_TYPE_PATTERN.match(text)
    if match:
        return is_type_text(match.group(1))
    parts = text.split("|")
    return len(set(parts)) == len(parts) and all(part in _JSON_TYPE_CHECKS for part in parts)


def value_matches_type(value: Any, text: str) -> bool:
    """YAML/JSON 值是否符合类型写法；text 须已通过 is_type_text"""
    match = _ARRAY_TYPE_PATTERN.match(text)
    if match:
        return isinstance(value, list) and all(value_matches_type(item, match.group(1)) for item in value)
    return any(_JSON_TYPE_CHECKS[part](value) for part in text.split("|"))


def parse_version(version: str) -> Tuple[int, ...]:
    """major.minor.patch 转成整数元组，用于比较大小"""
    return tuple(int(part) for part in version.split("."))


def _check_ref(value: Any) -> Any:
    parse_ref(value)
    return value


def _check_type(value: str) -> str:
    if not is_type_text(value):
        raise ValueError(
            _("类型写法不合规：{value}，应为 {types} 之一，或 array<类型>、string|integer 这样的组合").format(
                value=repr(value), types=", ".join(_JSON_TYPE_CHECKS)
            )
        )
    return value


def _check_version(value: str) -> str:
    if len(value) > SKILL_VERSION_MAX_LENGTH or not SKILL_VERSION_PATTERN.fullmatch(value):
        raise ValueError(_("版本号应为 major.minor.patch，如 1.0.0：{value}").format(value=value))
    return value


def _date_to_text(value: Any) -> Any:
    # YAML 会把不加引号的 2026-11-11、2026-11-11 10:30:00 解析成 date、datetime
    if isinstance(value, datetime.datetime):
        # 带时区或毫秒的转成 isoformat 文本，交给格式检查报错
        if value.tzinfo is None and not value.microsecond:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def _check_date(value: str) -> str:
    """YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，不带时区；日期和时间之间的 T 统一成空格"""
    try:
        if not _DATE_PATTERN.fullmatch(value):
            raise ValueError
        datetime.datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(
            _("应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS（不带时区）：{value}").format(value=value)
        ) from None
    return value.replace("T", " ")


def _check_text_not_empty(value: str) -> str:
    if not value.strip():
        raise ValueError(_("为空"))
    return value


ParamValue = Annotated[Any, AfterValidator(_check_ref)]
TypeText = Annotated[StrictStr, AfterValidator(_check_type)]
VersionText = Annotated[StrictStr, AfterValidator(_check_version)]
DateText = Annotated[StrictStr, BeforeValidator(_date_to_text), AfterValidator(_check_date)]


class _DeclarationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SkillInput(_DeclarationModel):
    """Skill 向用户收集的值；type 须与 with 绑定参数在资源定义中的类型一致，接口说明取自资源定义，
    这里只写 OpenAPI 里没有的编排信息
    """

    type: TypeText
    required: StrictBool
    # 编排提示：拟定规则、取值策略等；没有就不写
    description: StrictStr = ""
    example: Any
    default: Any = None

    @model_validator(mode="after")
    def _check_values_type(self) -> "SkillInput":
        if not value_matches_type(self.example, self.type):
            raise ValueError(_("example 与类型 {type} 不符").format(type=self.type))
        if self.has_default and not value_matches_type(self.default, self.type):
            raise ValueError(_("default 与类型 {type} 不符").format(type=self.type))
        return self

    @property
    def has_default(self) -> bool:
        return "default" in self.model_fields_set

    @property
    def omit_if_unset(self) -> bool:
        """选填且没有默认值：用户没给时整个参数不传"""
        return not self.required and not self.has_default


class SkillOutput(_DeclarationModel):
    """汇报给用户的字段；type 须与来源推出的类型一致，见 validator._RefChecker._check_output_types"""

    type: TypeText
    description: StrictStr
    value: StrictStr

    @field_validator("value")
    @classmethod
    def _check_value(cls, value: str) -> str:
        if parse_ref(value).kind == "value":
            raise ValueError(_("应为 ${{ inputs.<输入名> }} 或 ${{ steps.<步骤 id>.outputs.<字段路径> }}"))
        return value


def split_uses(uses: str) -> Tuple[str, str, str]:
    """`<网关>/<资源>@<环境>` -> (gateway, stage, resource)；不合规时抛 ValueError"""
    match = _USES_PATTERN.match(uses)
    if not match:
        raise ValueError(_("应为 <网关>/<资源>@<环境>：{uses}").format(uses=uses))
    gateway, resource, stage = match.groups()
    if not GATEWAY_NAME_PATTERN.fullmatch(gateway):
        raise ValueError(_("网关名不合规：{gateway}").format(gateway=gateway))
    if not RESOURCE_NAME_PATTERN.fullmatch(resource):
        raise ValueError(_("资源名不合规：{resource}").format(resource=resource))
    if not STAGE_NAME_PATTERN.fullmatch(stage):
        raise ValueError(_("环境名不合规：{stage}").format(stage=stage))
    return gateway, stage, resource


class SkillStep(_DeclarationModel):
    """一步调用一个接口；执行条件、轮询、逐个调用等写在 description 里"""

    id: StrictStr
    name: Optional[StrictStr] = None
    uses: StrictStr
    description: StrictStr
    with_: Dict[StrictStr, ParamValue] = Field(default_factory=dict, alias="with")

    @field_validator("id")
    @classmethod
    def _check_id(cls, value: str) -> str:
        if not SKILL_STEP_NAME_PATTERN.fullmatch(value):
            raise ValueError(_("步骤 id 不合规：{value}").format(value=value))
        return value

    @field_validator("uses")
    @classmethod
    def _check_uses(cls, value: str) -> str:
        split_uses(value)
        return value

    @field_validator("name", "description")
    @classmethod
    def _check_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError(_("为空"))
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
            raise ValueError(_("为空（没有内容写「无」）"))
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
            raise ValueError(_("输入名不合规：{names}").format(names=", ".join(invalid)))
        return value

    @field_validator("outputs")
    @classmethod
    def _check_outputs_not_empty(cls, value: Dict[str, SkillOutput]) -> Dict[str, SkillOutput]:
        # 可编排的资源都有响应字段，总有可汇报的结果
        if not value:
            raise ValueError(_("至少需要一个，写用户最终需要的结果"))
        return value

    @field_validator("steps")
    @classmethod
    def _check_step_ids(cls, value: List[SkillStep]) -> List[SkillStep]:
        ids = [step.id for step in value]
        duplicated = sorted({step_id for step_id in ids if ids.count(step_id) > 1})
        if duplicated:
            raise ValueError(_("步骤 id 重复：{ids}").format(ids=", ".join(duplicated)))
        return value

    @model_validator(mode="after")
    def _check_inputs_bound(self) -> "SkillOrchestration":
        bound = {
            parse_ref(value).name
            for step in self.steps
            for value in step.with_.values()
            if parse_ref(value).kind == "input"
        }
        unbound = [name for name in self.inputs if name not in bound]
        if unbound:
            raise ValueError(
                _("输入没有绑定到任何步骤的 with，类型无从校验、说明无从取得：{names}").format(
                    names=", ".join(unbound)
                )
            )
        return self

    def get_input(self, name: str) -> Optional[SkillInput]:
        return self.inputs.get(name)

    def is_omittable_input_ref(self, value: Any) -> bool:
        parsed = parse_ref(value)
        if parsed.kind != "input":
            return False
        item = self.get_input(parsed.name)
        return bool(item and item.omit_if_unset)


class SkillChangelogEntry(_DeclarationModel):
    version: VersionText
    date: DateText
    content: Annotated[StrictStr, AfterValidator(_check_text_not_empty)]


class SkillDeclaration(_DeclarationModel):
    name: StrictStr
    display_name: StrictStr
    display_name_en: Optional[StrictStr] = None
    description: StrictStr
    tags: List[StrictStr]
    version: VersionText
    # 从新到旧，第一条是当前版本
    changelog: List[SkillChangelogEntry]
    orchestration: SkillOrchestration

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if len(value) > SKILL_NAME_MAX_LENGTH or not SKILL_NAME_PATTERN.fullmatch(value):
            raise ValueError(_("不合规：{value}").format(value=value))
        return value

    @field_validator("display_name")
    @classmethod
    def _check_display_name(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= SKILL_DISPLAY_NAME_MAX_LENGTH:
            raise ValueError(_("长度应为 1–{max_length}").format(max_length=SKILL_DISPLAY_NAME_MAX_LENGTH))
        # 展示名会写成 SKILL.md 的一级标题，中间换行会拆开这一行
        if "\n" in value or "\r" in value:
            raise ValueError(_("不能包含换行"))
        return value

    @field_validator("display_name_en")
    @classmethod
    def _check_display_name_en(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not 1 <= len(value) <= SKILL_DISPLAY_NAME_MAX_LENGTH:
            raise ValueError(_("长度应为 1–{max_length}").format(max_length=SKILL_DISPLAY_NAME_MAX_LENGTH))
        return value

    @field_validator("description")
    @classmethod
    def _check_description(cls, value: str) -> str:
        if not 1 <= len(value) <= SKILL_DESCRIPTION_MAX_LENGTH:
            raise ValueError(_("长度应为 1–{max_length}").format(max_length=SKILL_DESCRIPTION_MAX_LENGTH))
        return value

    @field_validator("tags")
    @classmethod
    def _check_tags(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError(_("至少需要一个标签"))
        normalized = [normalize_tag_name(tag) for tag in value]
        for tag, name in zip(value, normalized):
            if not 1 <= len(name) <= SKILL_TAG_NAME_MAX_LENGTH:
                raise ValueError(
                    _("标签名长度应为 1–{max_length}：{tag}").format(
                        max_length=SKILL_TAG_NAME_MAX_LENGTH, tag=repr(tag)
                    )
                )
        for index, name in enumerate(normalized):
            if name in normalized[:index]:
                raise ValueError(_("标签规范化后重复：{name}").format(name=name))
        return value

    @field_validator("changelog")
    @classmethod
    def _check_changelog(cls, value: List[SkillChangelogEntry], info: ValidationInfo) -> List[SkillChangelogEntry]:
        if not value:
            raise ValueError(_("至少需要一条，第一条为当前版本"))
        # version 不合规时不在 info.data 里，已单独报错
        version = info.data.get("version")
        if version and value[0].version != version:
            raise ValueError(
                _("第一条应为当前版本 {version}，实际为 {actual}").format(version=version, actual=value[0].version)
            )
        for newer, older in zip(value, value[1:]):
            if parse_version(older.version) >= parse_version(newer.version):
                raise ValueError(
                    _("应按版本从新到旧排列且不重复：{newer} 之后是 {older}").format(
                        newer=newer.version, older=older.version
                    )
                )
        return value

    @property
    def current_changelog(self) -> SkillChangelogEntry:
        return self.changelog[0]

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
            raise SkillDeclarationError(
                [_("YAML 解析失败：{error}").format(error=" ".join(str(err).split()))]
            ) from None

    try:
        return SkillDeclaration.model_validate(data)
    except ValidationError as err:
        raise SkillDeclarationError([_format_error(item) for item in err.errors()]) from None


def _format_error(error: Dict[str, Any]) -> str:
    path = _format_loc(error["loc"]) or _("声明")
    if error["type"] == "value_error":
        message = str(error["ctx"]["error"])
    else:
        message = str(_ERROR_MESSAGES.get(error["type"], error["msg"]))
    return f"{path}: {message}"


def _format_loc(loc: Tuple[Union[str, int], ...]) -> str:
    text = ""
    for part in loc:
        if isinstance(part, int):
            text += f"[{part}]"
        else:
            text += f".{part}" if text else str(part)
    return text
