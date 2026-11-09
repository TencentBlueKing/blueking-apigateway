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
接口清单、输入输出、步骤，以及每次调用的 OpenAPI 3.1 片段。
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
from .refs import norm_path, parse_ref, poll_expr_paths, ref_text, ref_where
from .resource_definition import ResourceDefinition, ResourceParam, ResourceProvider
from .validator import ResourceKey, load_resources

if TYPE_CHECKING:
    from .declaration import SkillCall, SkillDeclaration, SkillOrchestration

PARAM_LOCATION_ORDER = {"path": 0, "query": 1, "header": 2, "body": 3}
NOTATION_PLACES = ("path", "query", "header")


class SkillRenderError(Exception):
    pass


@dataclass
class RenderResult:
    body: str
    warnings: List[str] = field(default_factory=list)


def render_skill_body(declaration: SkillDeclaration, provider: ResourceProvider) -> RenderResult:
    """渲染正文；调用方需先完成校验，编排引用的资源都存在时才能渲染"""
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
            "inputs": orchestration.inputs,
            "outputs": self._outputs(),
            "steps": self._steps(),
            "notation": self._notation(),
            "has_write": any(resource.method in WRITE_METHODS for resource in self.resources.values()),
        }

    def _looped_calls(self) -> set:
        return {(step.name, call.resource) for step, call in self.orchestration.iter_calls() if call.for_each}

    def _outputs(self) -> List[Dict[str, Any]]:
        looped = self._looped_calls()
        outputs = []
        for output in self.orchestration.outputs:
            parsed = parse_ref(output.from_)
            outputs.append(
                {
                    "name": output.name,
                    "type": output.type,
                    "description": output.description,
                    "source": output.from_,
                    "looped": parsed.kind == "call" and (parsed.step, parsed.resource) in looped,
                }
            )
        return outputs

    def _steps(self) -> List[Dict[str, Any]]:
        used_fields = _used_response_fields(self.orchestration)
        steps, index = [], 0
        for step in self.orchestration.steps:
            calls = []
            for call in step.calls:
                index += 1
                resource = self.resources[call.key]
                calls.append(
                    {
                        "index": index,
                        "resource": call.resource,
                        "for_each": call.for_each,
                        "openapi": _render_operation(
                            self.orchestration, call, resource, used_fields.get((step.name, call.resource), [])
                        ),
                        "credentials": [
                            param.name
                            for param in resource.params
                            if param.name in CREDENTIAL_PARAMS and param.name not in call.params
                        ],
                        "unmapped": [
                            param.name
                            for param in resource.params
                            if param.required and param.name not in call.params and param.name not in CREDENTIAL_PARAMS
                        ],
                        "poll": call.poll,
                        "poll_has_streak": bool(call.poll)
                        and any(times > 1 for _, times in call.poll.stop_conditions),  # type: ignore[union-attr]
                    }
                )
            steps.append({"name": step.name, "description": step.description, "calls": calls})
        return steps

    def _notation(self) -> Dict[str, Any]:
        """本 Skill 的取值和 OpenAPI 片段里实际出现的写法，说明里只写这些"""
        calls = [call for _, call in self.orchestration.iter_calls()]
        call_refs = [ref for call in calls for ref in call.params.values()]
        texts = [ref_text(ref) for ref in call_refs]
        texts += [output.from_ for output in self.orchestration.outputs]
        texts += [call.for_each.from_ for call in calls if call.for_each]
        refs = [text for text in texts if text]

        locations = set()
        for call in calls:
            resource = self.resources[call.key]
            locations |= {resource.get_param_location(name) for name in call.params}

        return {
            "places": [place for place in NOTATION_PLACES if place in locations],
            "body": "body" in locations,
            "index": any(re.search(r"\[\d+\]", ref) for ref in refs),
            "all": any("[]" in ref for ref in refs),
            "each": any(ref.startswith("each.") for ref in refs),
            "call": any(parse_ref(ref).kind == "call" for ref in refs),
            "value": any(parse_ref(ref).kind == "value" for ref in call_refs),
            "where": any(ref_where(ref) for ref in call_refs),
            "omit": any(self.orchestration.is_omittable_input_ref(ref) for ref in call_refs),
        }


def _used_response_fields(orchestration: SkillOrchestration) -> Dict[Tuple[str, str], List[str]]:
    """每个 (step, resource) 要读的响应字段：本调用 reads 和 poll 用到的，以及被后续 for_each / params / outputs 直接引用的。

    逐个调用通过 each.* 用到的子字段写在那次调用的参数表里，这里不再列；列了子字段时不再单独列它的前缀。
    """
    used: Dict[Tuple[str, str], List[str]] = {}

    def add(step: str, resource: str, path: str) -> None:
        paths = used.setdefault((step, resource), [])
        if path not in paths:
            paths.append(path)

    def add_ref(ref: Any) -> None:
        parsed = parse_ref(ref)
        if parsed.kind == "call":
            add(parsed.step, parsed.resource, parsed.path)

    for step, call in orchestration.iter_calls():
        poll_paths = poll_expr_paths(call.poll.exprs) if call.poll else []
        for path in call.reads + poll_paths:
            add(step.name, call.resource, path)
        if call.for_each:
            add_ref(call.for_each.from_)
        for ref in call.params.values():
            add_ref(ref)
    for output in orchestration.outputs:
        add_ref(output.from_)

    for key, paths in used.items():
        normed = [norm_path(path) for path in paths]
        used[key] = [
            path
            for path, current in zip(paths, normed)
            if not any(other != current and other.startswith((current + ".", current + "[")) for other in normed)
        ]
    return used


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


def _binding_fields(orchestration: SkillOrchestration, ref: Any) -> Dict[str, Any]:
    parsed = parse_ref(ref)
    fields: Dict[str, Any] = {"x-value": parsed.value} if parsed.kind == "value" else {"x-from": ref_text(ref)}
    where = ref_where(ref)
    if where:
        fields["x-where"] = where
    if orchestration.is_omittable_input_ref(ref):
        fields["x-omit-if-unset"] = True
    return fields


def _response_schema(resource: ResourceDefinition, paths: List[str]) -> Dict[str, Any]:
    """把要读的响应字段路径（data.records[0].id）还原成嵌套的 JSON Schema，只含这些字段"""
    root: Dict[str, Any] = {"type": "object", "properties": {}}
    for path in paths:
        parts = norm_path(path).split(".")
        node, sofar = root, ""
        for index, segment in enumerate(parts):
            is_array = segment.endswith("[]")
            name = segment[:-2] if is_array else segment
            sofar = f"{sofar}.{segment}" if sofar else segment
            props = node.setdefault("properties", {})
            if index == len(parts) - 1 and not is_array:
                meta = resource.get_response_field(sofar)
                if meta:
                    props[name] = _Flow(_type_schema(meta.type), description=meta.description)
                elif resource.has_response_array(sofar):
                    props[name] = _Flow(type="array")
                else:
                    props[name] = _Flow(type="object")
                continue
            child = props.get(name)
            if child is None or isinstance(child, _Flow):
                child = {"type": "array", "items": {"type": "object"}} if is_array else {"type": "object"}
                props[name] = child
            node = child["items"] if is_array else child
    return root


def _param_spec(resource: ResourceDefinition, name: str) -> ResourceParam:
    return resource.get_param(name) or ResourceParam(name=name, location=resource.get_param_location(name))


def _build_params(
    orchestration: SkillOrchestration, call: SkillCall, resource: ResourceDefinition
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """按 path、query、header、body 的顺序（path 参数按在路径里出现的顺序）生成 parameters 和 body 属性"""

    def order(item: Tuple[str, Any]) -> Tuple[int, int]:
        location = resource.get_param_location(item[0])
        position = resource.path.find("{" + item[0] + "}") if location == "path" else 0
        return PARAM_LOCATION_ORDER.get(location, 9), position

    params: List[Dict[str, Any]] = []
    body: Dict[str, Any] = {}
    body_required: List[str] = []
    for name, ref in sorted(call.params.items(), key=order):
        spec = _param_spec(resource, name)
        required = spec.required or spec.location == "path"
        schema: Optional[_Flow] = _type_schema(spec.type) if spec.type else None
        if spec.location == "body":
            prop: Dict[str, Any] = dict(schema or {})
            if spec.description:
                prop["description"] = spec.description
            prop.update(_binding_fields(orchestration, ref))
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
        item.update(_binding_fields(orchestration, ref))
        params.append(item)
    return params, body, body_required


def _render_operation(
    orchestration: SkillOrchestration, call: SkillCall, resource: ResourceDefinition, response_paths: List[str]
) -> str:
    params, body, body_required = _build_params(orchestration, call, resource)
    operation: Dict[str, Any] = {
        "operationId": call.resource,
        "x-bk-gateway": call.gateway,
        "x-bk-stage": call.stage,
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
    if response_paths:
        operation["responses"] = {
            "200": {
                "description": "只列本 Skill 要读的字段",
                "content": {"application/json": {"schema": _response_schema(resource, response_paths)}},
            }
        }

    doc = {"paths": {resource.path: {resource.method.lower(): operation}}}
    text = yaml.dump(doc, Dumper=_OpenAPIDumper, allow_unicode=True, sort_keys=False, width=10000)
    return text.rstrip("\n")
