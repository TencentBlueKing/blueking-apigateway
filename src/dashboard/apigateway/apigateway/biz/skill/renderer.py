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
接口清单、输入输出、步骤，以及每一步的 YAML 调用说明。步骤 description 原样写出。
"""

import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple

import yaml
from django.utils.translation import gettext as _
from jinja2 import FileSystemLoader, StrictUndefined, Template
from jinja2.sandbox import SandboxedEnvironment

from .constants import (
    SKILL_BODY_MAX_LINES,
    SKILL_BODY_TEMPLATE_NAME,
    SKILL_TEMPLATES_DIR,
    WRITE_METHODS,
)
from .refs import each_array, parse_ref
from .validator import ResourceKey, input_bindings, load_resources

if TYPE_CHECKING:
    from .declaration import SkillDeclaration, SkillOrchestration, SkillStep
    from .resource_loader import ResourceProvider, SkillResource
    from .schema_converter import ResourceParam

PARAM_LOCATION_ORDER = {"path": 0, "query": 1, "header": 2, "body": 3}


class SkillRenderError(Exception):
    pass


@dataclass
class RenderResult:
    body: str
    warnings: List[str] = field(default_factory=list)


def render_skill_body(declaration: SkillDeclaration, provider: ResourceProvider) -> RenderResult:
    """渲染正文；调用方需先完成校验，没有 error、编排引用的资源都存在时才能渲染

    例如：syncer 校验通过后调用，返回的 body 写入 SkillVersion.artifact["SKILL.md"]；
    正文超过 SKILL_BODY_MAX_LINES 行时只加 warning，不报错
    """
    resources, missing = load_resources(declaration.orchestration, provider)
    if missing:
        details = "; ".join(f"{item.gateway}.{item.resource}@{item.stage}: {item.reason}" for item in missing)
        raise SkillRenderError(_("资源不可编排，不能渲染：{details}").format(details=details))

    context = _SkillBodyContext(declaration, resources).build()  # type: ignore[arg-type]
    body = _get_template().render(**context)

    result = RenderResult(body=body)
    lines = len(body.splitlines())
    if lines > SKILL_BODY_MAX_LINES:
        result.warnings.append(
            _("SKILL.md 正文 {lines} 行，超过 {max_lines} 行").format(lines=lines, max_lines=SKILL_BODY_MAX_LINES)
        )
    return result


@lru_cache(maxsize=1)
def _get_template() -> Template:
    """加载 SKILL.md.j2 并注册过滤器；进程内只加载一次"""
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
    r"""表格单元格文本：空值写成 -，非字符串写成 JSON 行内代码，转义 | 并把换行换成空格

    例如：
        None、"" -> "-"
        "1|2" -> "1\|2"
        2 -> "`2`"
        {"a": 1} -> '`{"a": 1}`'
    """
    if value is None or value == "":
        return "-"
    if not isinstance(value, str):
        return f"`{json.dumps(value, ensure_ascii=False)}`"
    return value.replace("|", "\\|").replace("\n", " ")


def code_cell(value: Any) -> str:
    r"""表格单元格里的 JSON 值，写成行内代码；非空字符串不加引号，null、空字符串写成 `null`、`""`，与表示未配置的 - 区分。
    行内代码里的 | 也会拆开表格，同样转义

    例如：
        "abc" -> "`abc`"
        "" -> '`""`'
        None -> "`null`"
        "a|b" -> "`a\|b`"
    """
    text = value if isinstance(value, str) and value else json.dumps(value, ensure_ascii=False)
    text = text.replace("|", "\\|")
    return f"`{text}`"


def yn(flag: bool) -> str:
    """布尔值写成「是」「否」，用于接口清单的认证、权限列

    例如：True -> "是"；False -> "否"
    """
    return "是" if flag else "否"


def backtick(value: str) -> str:
    """包成行内代码

    例如："bk_biz_id" -> "`bk_biz_id`"
    """
    return f"`{value}`"


# ---------- 模板上下文 ----------


class _SkillBodyContext:
    def __init__(self, declaration: SkillDeclaration, resources: Dict[ResourceKey, SkillResource]):
        self.declaration = declaration
        self.orchestration: SkillOrchestration = declaration.orchestration
        self.resources = resources

    def build(self) -> Dict[str, Any]:
        """模板上下文；键名对应 SKILL.md.j2 里的变量"""
        orchestration = self.orchestration
        return {
            "display_name": self.declaration.display_name,
            "description": orchestration.description,
            "guide": orchestration.guide,
            "resources": self._resources(),
            "inputs": self._inputs(),
            "outputs": [
                {"name": name, "type": item.type, "description": item.description, "source": item.value}
                for name, item in orchestration.outputs.items()
            ],
            "steps": self._steps(),
            "has_write": any(resource.data.method in WRITE_METHODS for resource in self.resources.values()),
        }

    def _resources(self) -> List[Dict[str, Any]]:
        """接口清单一行。认证五项直接取发布资源，不在 SkillResource 上再抄一份。"""
        rows = []
        for resource in self.resources.values():
            data = resource.data
            rows.append(
                {
                    "resource": data.name,
                    "gateway": resource.gateway,
                    "stage": resource.stage,
                    "method": data.method,
                    "path": data.path,
                    "description": data.description,
                    "user_verified_required": data.verified_user_required,
                    "app_verified_required": data.verified_app_required,
                    "resource_perm_required": data.resource_perm_required,
                    "oauth2_public_client_enabled": data.oauth2_public_client_enabled,
                    "oauth2_personal_client_enabled": data.oauth2_personal_client_enabled,
                }
            )
        return rows

    def _inputs(self) -> List[Dict[str, Any]]:
        """输入表的行：说明取自绑定参数的 OpenAPI 定义，声明里的说明单列为编排提示

        例如：输入 bk_scope_id 绑定的两个参数说明为「资源范围 ID」「资源范围 ID，与 bk_scope_type 对应」时，
        description 只保留后一条，hint 是声明里该输入的 description
        """
        bindings = input_bindings(self.orchestration, self.resources)
        return [
            {
                "name": name,
                "type": item.type,
                "required": item.required,
                "description": "；".join(_distinct_descriptions(item.param.description for item in bindings[name])),
                "hint": item.description,
                "example": item.example,
                "default": item.default,
                "has_default": item.has_default,
            }
            for name, item in self.orchestration.inputs.items()
        ]

    def _steps(self) -> List[Dict[str, Any]]:
        """执行步骤表和每步正文：序号、标题、说明和 YAML 调用说明

        例如：第 1 步 id 为 run、资源为 execute_job_plan、name 为「执行方案」时，
        标题为「1. run / execute_job_plan：执行方案」
        """
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
                    "description": step.description,
                    "call": _render_call(self.orchestration, step, resource),
                }
            )
        return steps


def _distinct_descriptions(descriptions: Iterable[str]) -> List[str]:
    """去掉空的、重复的，以及被另一条完整包含的说明

    例如：["资源范围 ID", "", "资源范围 ID，与 bk_scope_type 对应", "资源范围 ID"] -> ["资源范围 ID，与 bk_scope_type 对应"]
    """
    items = list(dict.fromkeys(text for text in descriptions if text))
    return [text for text in items if not any(text != other and text in other for other in items)]


# ---------- OpenAPI 片段 ----------


class _Flow(dict):
    """输出成一行 {k: v} 的映射"""


class _FlowList(list):
    """输出成一行 [a, b] 的列表"""


class _OpenAPIDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        """列表项比父键多缩进一级，PyYAML 默认的 `- ` 与父键对齐

        例如：输出 "parameters:\\n  - name: id"，而不是 "parameters:\\n- name: id"
        """
        return super().increase_indent(flow, False)

    def ignore_aliases(self, data):
        """同一个对象出现多次时照写，不生成 &id001、*id001 锚点"""
        return True


_OpenAPIDumper.add_representer(
    _Flow, lambda dumper, value: dumper.represent_mapping("tag:yaml.org,2002:map", value, flow_style=True)
)
_OpenAPIDumper.add_representer(
    _FlowList, lambda dumper, value: dumper.represent_sequence("tag:yaml.org,2002:seq", value, flow_style=True)
)


def _flow(value: Any, block: bool = False) -> Any:
    """复制 schema：含 properties 或块格式子节点（恰为 dict / list）的按块输出，其余写成一行

    例如：
        {"type": "string", "enum": ["a", "b"]} -> 一行 {type: string, enum: [a, b]}
        {"type": "object", "properties": {"id": {"type": "integer"}}} -> 外层按块输出，id 写成一行 {type: integer}
    """
    if isinstance(value, dict):
        items = {key: _flow(item, key == "properties") for key, item in value.items()}
        if block or "properties" in items or any(type(item) in (dict, list) for item in items.values()):
            return items
        return _Flow(items)
    if isinstance(value, list):
        elements = [_flow(item) for item in value]
        return elements if any(type(item) in (dict, list) for item in elements) else _FlowList(elements)
    return value


def _binding_fields(orchestration: SkillOrchestration, value: Any, param: ResourceParam) -> Dict[str, Any]:
    """参数取值 -> 调用说明里的绑定字段：固定值写 x-value，引用写 x-from，逐个调用加 x-each，
    选填且没有默认值的输入加 x-omit-if-unset

    例如：
        2 -> {"x-value": 2}
        "${{ inputs.keyword }}"，keyword 选填、没有 default -> {"x-from": "${{ inputs.keyword }}", "x-omit-if-unset": True}
        "${{ steps.list-tasks.outputs.data[].id }}"，参数为 integer -> {"x-from": "...", "x-each": True}
    """
    parsed = parse_ref(value)
    fields: Dict[str, Any] = {"x-value": parsed.value} if parsed.kind == "value" else {"x-from": value}
    if each_array(value, param.type):
        fields["x-each"] = True
    if orchestration.is_omittable_input_ref(value):
        fields["x-omit-if-unset"] = True
    return fields


def _get_param(resource: SkillResource, name: str) -> ResourceParam:
    """按名字取资源定义中的参数，位置和类型以定义为准；不在定义中时抛 SkillRenderError，校验阶段已报 error

    例如：get_task_status 定义了 path 参数 task_id -> 返回该参数；取 foo -> SkillRenderError
    """
    param = resource.get_param(name)
    if param is None:
        raise SkillRenderError(
            _("{gateway}.{resource} 的资源定义中没有参数 {name}，不能渲染").format(
                gateway=resource.gateway, resource=resource.data.name, name=name
            )
        )
    return param


def _build_params(
    orchestration: SkillOrchestration, step: SkillStep, resource: SkillResource
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """按 path、query、header、body 的顺序（path 参数按在路径里出现的顺序）生成 parameters 和 body 属性。
    参数 schema 照抄已发布的定义，嵌套字段、required、enum 等约束都保留；定义里写了的 style、explode、allowReserved 也照抄。

    例如：with 绑定 body 参数 name、query 参数 limit、path 参数 task_id 时，
    parameters 依次为 task_id（required）、limit，body 为 {"name": {...}}
    """

    def order(name: str) -> Tuple[int, int]:
        """排序键：(位置序号, path 参数在路径中的下标)

        例如：路径 /tasks/{bk_biz_id}/{task_id}/ 里 bk_biz_id 排在 task_id 前，query 参数排在所有 path 参数后
        """
        location = _get_param(resource, name).location
        position = resource.data.path.find("{" + name + "}") if location == "path" else 0
        return PARAM_LOCATION_ORDER.get(location, 9), position

    params: List[Dict[str, Any]] = []
    body: Dict[str, Any] = {}
    body_required: List[str] = []
    for name in sorted(step.with_, key=order):
        spec = _get_param(resource, name)
        required = spec.required or spec.location == "path"
        # 顶层说明统一用 spec.description 写在参数上；顶层 x- 扩展会和绑定写法（x-from、x-each 等）混在一起
        schema = _flow(
            {key: value for key, value in spec.schema.items() if key != "description" and not key.startswith("x-")}
        )
        binding = _binding_fields(orchestration, step.with_[name], spec)
        if spec.location == "body":
            prop: Dict[str, Any] = dict(schema)
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
        # 数组、对象取值的拼接方式（如 explode: false 时逗号分隔）只写在这里，丢掉后调用方会按默认方式拼接
        item.update(spec.serialization)
        # OpenAPI 3.1 的 Parameter 必须有 schema 或 content，定义里没写类型时为 {}
        item["schema"] = schema
        item.update(binding)
        params.append(item)
    return params, body, body_required


def _render_call(orchestration: SkillOrchestration, step: SkillStep, resource: SkillResource) -> str:
    """一步的 YAML 调用说明：调用目标、parameters、requestBody 和 responses

    例如：bk-sops/get_task_status@prod 绑定 task_id 时，依次写出 gateway_name、stage_name、resource_name、
    method、path，parameters 里一项 task_id（in: path），responses 照抄已发布的第一个 2xx 响应 schema；
    请求体必须发送时即使没有绑定字段也写出 requestBody
    """
    params, body, body_required = _build_params(orchestration, step, resource)
    call: Dict[str, Any] = {
        "gateway_name": step.gateway,
        "stage_name": step.stage,
        "resource_name": step.resource,
        "method": resource.data.method,
        "path": resource.data.path,
    }
    if params:
        call["parameters"] = params
    # 请求体必须发送时，没有绑定任何属性也要写出 requestBody，调用方发 {}
    if body or resource.body_required:
        body_schema: Dict[str, Any] = {"type": "object"}
        if body_required:
            body_schema["required"] = _FlowList(body_required)
        body_schema["properties"] = body
        call["requestBody"] = {
            "required": resource.body_required or bool(body_required),
            "content": {"application/json": {"schema": body_schema}},
        }
    if resource.response_schema:
        call["responses"] = {
            "200": {
                "description": "已发布接口的响应字段",
                "content": {"application/json": {"schema": _flow(resource.response_schema)}},
            }
        }

    text = yaml.dump(call, Dumper=_OpenAPIDumper, allow_unicode=True, sort_keys=False, width=10000)
    return text.rstrip("\n")
