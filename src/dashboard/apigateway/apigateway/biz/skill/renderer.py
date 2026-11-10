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
"""SKILL.md 正文渲染。

章节、顺序和固定文案在 data/skill/templates/SKILL.md.j2；这里只计算模板用到的数据：
接口清单、输入输出、步骤，以及每一步的 OpenAPI 3.1 片段。步骤的 if 和 description 原样写出。
"""

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import yaml
from jinja2 import FileSystemLoader, StrictUndefined, Template
from jinja2.sandbox import SandboxedEnvironment

from .constants import (
    CREDENTIAL_PARAMS,
    SKILL_BODY_MAX_LINES,
    SKILL_BODY_TEMPLATE_NAME,
    SKILL_TEMPLATES_DIR,
    WRITE_METHODS,
)
from .refs import norm_path, parse_ref
from .validator import ResourceKey, load_resources

if TYPE_CHECKING:
    from .declaration import SkillDeclaration, SkillOrchestration, SkillStep
    from .resource_definition import ResourceDefinition, ResourceParam, ResourceProvider

PARAM_LOCATION_ORDER = {"path": 0, "query": 1, "header": 2, "body": 3}
NOTATION_PLACES = ("path", "query", "header")


class SkillRenderError(Exception):
    pass


@dataclass
class RenderResult:
    body: str
    warnings: List[str] = field(default_factory=list)


def render_skill_body(declaration: SkillDeclaration, provider: ResourceProvider) -> RenderResult:
    """渲染正文；调用方需先完成校验，没有 error、编排引用的资源都存在时才能渲染"""
    resources = load_resources(declaration.orchestration, provider)
    missing = [".".join(key) for key, resource in resources.items() if resource is None]
    if missing:
        raise SkillRenderError(f"资源不存在，不能渲染：{'、'.join(missing)}")

    context = _SkillBodyContext(declaration, resources).build()  # type: ignore[arg-type]
    body = _get_template().render(**context)

    result = RenderResult(body=body)
    lines = len(body.splitlines())
    if lines > SKILL_BODY_MAX_LINES:
        result.warnings.append(f"SKILL.md 正文 {lines} 行，超过 {SKILL_BODY_MAX_LINES} 行")
    return result


@lru_cache(maxsize=1)
def _get_template() -> Template:
    # 输出是 Markdown，不能做 HTML 转义
    env = SandboxedEnvironment(  # noqa: S701
        loader=FileSystemLoader(str(SKILL_TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters.update(md_cell=md_cell, code_cell=code_cell, yn=yn, backtick=backtick)
    return env.get_template(SKILL_BODY_TEMPLATE_NAME)


# ---------- 模板过滤器 ----------


def md_cell(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if not isinstance(value, str):
        return f"`{json.dumps(value, ensure_ascii=False)}`"
    return value.replace("|", "\\|").replace("\n", " ")


def code_cell(value: Any) -> str:
    if value is None or value == "":
        return "-"
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return f"`{text}`"


def yn(flag: bool) -> str:
    return "是" if flag else "否"


def backtick(value: str) -> str:
    return f"`{value}`"


# ---------- 模板上下文 ----------


class _SkillBodyContext:
    def __init__(self, declaration: SkillDeclaration, resources: Dict[ResourceKey, ResourceDefinition]):
        self.declaration = declaration
        self.orchestration: SkillOrchestration = declaration.orchestration
        self.resources = resources

    def build(self) -> Dict[str, Any]:
        orchestration = self.orchestration
        return {
            "display_name": self.declaration.display_name,
            "description": orchestration.description,
            "guide": orchestration.guide,
            "resources": list(self.resources.values()),
            "inputs": self._inputs(),
            "outputs": [
                {"name": name, "type": item.type, "description": item.description, "source": item.value}
                for name, item in orchestration.outputs.items()
            ],
            "steps": self._steps(),
            "notation": self._notation(),
            "has_write": any(resource.method in WRITE_METHODS for resource in self.resources.values()),
        }

    def _inputs(self) -> List[Dict[str, Any]]:
        """保留声明里的编排说明，并追加绑定参数在 OpenAPI 中的完整说明。"""
        descriptions: Dict[str, List[str]] = {name: [] for name in self.orchestration.inputs}
        for step in self.orchestration.steps:
            resource = self.resources[step.key]
            for param_name, value in step.with_.items():
                ref = parse_ref(value)
                if ref.kind != "input":
                    continue
                param = _get_param(resource, param_name)
                if param.description and param.description not in descriptions[ref.name]:
                    descriptions[ref.name].append(param.description)

        inputs = []
        for name, item in self.orchestration.inputs.items():
            data = {"name": name, **item.model_dump()}
            if descriptions[name]:
                data["description"] = f"{item.description}；OpenAPI 参数说明：{'；'.join(descriptions[name])}"
            inputs.append(data)
        return inputs

    def _steps(self) -> List[Dict[str, Any]]:
        steps = []
        for index, step in enumerate(self.orchestration.steps, 1):
            resource = self.resources[step.key]
            title = f"{index}. {step.id} / {step.resource}"
            if step.name:
                title += f"：{step.name}"
            steps.append(
                {
                    "index": index,
                    "id": step.id,
                    "name": step.name,
                    "resource": step.resource,
                    "title": title,
                    "condition": step.if_,
                    "description": step.description,
                    "openapi": _render_operation(self.orchestration, step, resource),
                    "credentials": [
                        param.name
                        for param in resource.params
                        if param.name in CREDENTIAL_PARAMS and param.name not in step.with_
                    ],
                    "unmapped": _unmapped_params(step, resource),
                }
            )
        return steps

    def _notation(self) -> Dict[str, Any]:
        """本 Skill 的取值和 OpenAPI 片段里实际出现的写法，说明里只写这些"""
        steps = self.orchestration.steps
        values = [value for step in steps for value in step.with_.values()]
        refs = [value for value in values if parse_ref(value).kind != "value"]
        refs += [output.value for output in self.orchestration.outputs.values()]

        locations, unmapped = set(), False
        for step in steps:
            resource = self.resources[step.key]
            names = _unmapped_params(step, resource)
            unmapped = unmapped or bool(names)
            locations |= {_get_param(resource, name).location for name in [*step.with_, *names]}

        return {
            "places": [place for place in NOTATION_PLACES if place in locations],
            "body": "body" in locations,
            "index": any(re.search(r"\[\d+\]", ref) for ref in refs),
            "all": any("[]" in ref for ref in refs),
            "step": any(parse_ref(ref).kind == "step" for ref in refs),
            "value": any(parse_ref(value).kind == "value" for value in values),
            "omit": any(self.orchestration.is_omittable_input_ref(value) for value in values),
            "unmapped": unmapped,
            "condition": any(step.if_ for step in steps),
        }


def _unmapped_params(step: SkillStep, resource: ResourceDefinition) -> List[str]:
    """资源定义里必填、with 没写的参数（认证凭据除外），取值由步骤说明交代"""
    return [
        param.name
        for param in resource.params
        if (param.required or param.location == "path")
        and param.name not in step.with_
        and param.name not in CREDENTIAL_PARAMS
    ]


# ---------- OpenAPI 片段 ----------


class _Flow(dict):
    """输出成一行 {k: v} 的映射"""


class _FlowList(list):
    """输出成一行 [a, b] 的列表"""


class _OpenAPIDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

    def ignore_aliases(self, data):
        return True


_OpenAPIDumper.add_representer(
    _Flow, lambda dumper, value: dumper.represent_mapping("tag:yaml.org,2002:map", value, flow_style=True)
)
_OpenAPIDumper.add_representer(
    _FlowList, lambda dumper, value: dumper.represent_sequence("tag:yaml.org,2002:seq", value, flow_style=True)
)


def _type_schema(type_text: str) -> _Flow:
    """资源定义里的类型写法（string、array<string>、array|integer|string）-> JSON Schema"""
    match = re.fullmatch(r"array<(.+)>", type_text)
    if match:
        return _Flow(type="array", items=_type_schema(match.group(1)))
    if "|" in type_text:
        return _Flow(type=_FlowList(type_text.split("|")))
    return _Flow(type=type_text)


def _binding_fields(orchestration: SkillOrchestration, value: Any) -> Dict[str, Any]:
    parsed = parse_ref(value)
    fields: Dict[str, Any] = {"x-value": parsed.value} if parsed.kind == "value" else {"x-from": value}
    if orchestration.is_omittable_input_ref(value):
        fields["x-omit-if-unset"] = True
    return fields


class _ResponseNode:
    """把扁平的响应字段路径还原成嵌套 schema，父字段说明和子字段都保留。"""

    def __init__(self) -> None:
        self.type = ""
        self.description = ""
        self.properties: Dict[str, _ResponseNode] = {}
        self.item: Optional[_ResponseNode] = None

    def place(self, path: str, type_text: str, description: str) -> None:
        node = self
        parts = [part for part in norm_path(path).split(".") if part]
        for index, part in enumerate(parts):
            is_array = part.endswith("[]")
            name = part[:-2] if is_array else part
            child = node.properties.setdefault(name, _ResponseNode())
            if is_array:
                item = child._ensure_array()
                if index == len(parts) - 1:
                    child.apply(type_text, description)
                node = item
                continue
            if index == len(parts) - 1:
                child.apply(type_text, description)
                return
            if not child.type:
                child.type = "object"
            node = child

    def apply(self, type_text: str, description: str) -> None:
        if description:
            self.description = description
        if type_text == "array" or type_text.startswith("array<"):
            item = self._ensure_array()
            inner = type_text[6:-1] if type_text.startswith("array<") and type_text.endswith(">") else ""
            if inner:
                item.apply(inner, "")
            elif not item.type and not item.properties:
                item.type = "object"
            return
        if self.properties or self.item is not None:
            if not self.type:
                self.type = "object"
            return
        self.type = type_text or "object"

    def to_schema(self) -> Any:
        if self.item is not None or self.type == "array":
            items = self.item.to_schema() if self.item is not None else _Flow(type="object")
            if isinstance(items, dict) and "properties" in items:
                schema: Dict[str, Any] = {"type": "array"}
                if self.description:
                    schema["description"] = self.description
                schema["items"] = items
                return schema
            schema = _Flow(type="array", items=items)
            if self.description:
                schema["description"] = self.description
            return schema
        if self.properties:
            schema = {"type": self.type or "object"}
            if self.description:
                schema["description"] = self.description
            schema["properties"] = {name: child.to_schema() for name, child in self.properties.items()}
            return schema
        schema = _type_schema(self.type or "object")
        if self.description:
            schema["description"] = self.description
        return schema

    def _ensure_array(self) -> _ResponseNode:
        self.type = "array"
        if self.item is None:
            self.item = _ResponseNode()
        return self.item


def _response_schema(resource: ResourceDefinition) -> Dict[str, Any]:
    """用资源定义里的全部响应字段还原 JSON Schema。"""
    root = _ResponseNode()
    root.type = "object"
    for item in resource.responses:
        root.place(item.field, item.type, item.description)
    return root.to_schema()


def _get_param(resource: ResourceDefinition, name: str) -> ResourceParam:
    """参数必须在资源定义中，位置和类型以定义为准；不在定义中的参数校验已报 error"""
    param = resource.get_param(name)
    if param is None:
        raise SkillRenderError(f"{resource.gateway}.{resource.resource} 的资源定义中没有参数 {name}，不能渲染")
    return param


def _build_params(
    orchestration: SkillOrchestration, step: SkillStep, resource: ResourceDefinition
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """按 path、query、header、body 的顺序（path 参数按在路径里出现的顺序）生成 parameters 和 body 属性；
    必填但没写进 with 的参数也列出，不带取值
    """

    def order(name: str) -> Tuple[int, int]:
        location = _get_param(resource, name).location
        position = resource.path.find("{" + name + "}") if location == "path" else 0
        return PARAM_LOCATION_ORDER.get(location, 9), position

    params: List[Dict[str, Any]] = []
    body: Dict[str, Any] = {}
    body_required: List[str] = []
    for name in sorted([*step.with_, *_unmapped_params(step, resource)], key=order):
        spec = _get_param(resource, name)
        required = spec.required or spec.location == "path"
        schema: Optional[_Flow] = _type_schema(spec.type) if spec.type else None
        binding = _binding_fields(orchestration, step.with_[name]) if name in step.with_ else {}
        if spec.location == "body":
            prop: Dict[str, Any] = dict(schema or {})
            if spec.description:
                prop["description"] = spec.description
            prop.update(binding)
            body[name] = prop
            if required:
                body_required.append(name)
            continue
        item: Dict[str, Any] = {"name": name, "in": spec.location}
        if required:
            item["required"] = True
        if spec.description:
            item["description"] = spec.description
        if schema:
            item["schema"] = schema
        item.update(binding)
        params.append(item)
    return params, body, body_required


def _render_operation(orchestration: SkillOrchestration, step: SkillStep, resource: ResourceDefinition) -> str:
    params, body, body_required = _build_params(orchestration, step, resource)
    operation: Dict[str, Any] = {
        "operationId": step.resource,
        "x-bk-gateway": step.gateway,
        "x-bk-stage": step.stage,
    }
    if params:
        operation["parameters"] = params
    if body:
        body_schema: Dict[str, Any] = {"type": "object"}
        if body_required:
            body_schema["required"] = _FlowList(body_required)
        body_schema["properties"] = body
        operation["requestBody"] = {
            "required": bool(body_required),
            "content": {"application/json": {"schema": body_schema}},
        }
    if resource.responses:
        operation["responses"] = {
            "200": {
                "description": "已发布接口的响应字段",
                "content": {"application/json": {"schema": _response_schema(resource)}},
            }
        }

    doc = {"paths": {resource.path: {resource.method.lower(): operation}}}
    text = yaml.dump(doc, Dumper=_OpenAPIDumper, allow_unicode=True, sort_keys=False, width=10000)
    return text.rstrip("\n")
