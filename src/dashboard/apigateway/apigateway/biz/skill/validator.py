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
"""声明的完整校验：编排前后引用关系，以及编排与资源定义的对照。

资源定义（目标环境当前发布版本的 OpenAPI schema）是参数和响应的唯一依据，声明只引用、不重新定义：
输入声明的类型必须与 with 绑定的参数一致。必填参数没有写进 with、参数不在定义中、引用的响应字段不在定义中、
输入类型与绑定参数不一致、必填参数取自可能不传的输入、同一步逐个调用的参数取自不同数组、输出类型与来源不一致，都是 error。
结构和字段规则已在解析声明时检查，见 declaration.py。步骤 description 是自然语言，不校验。
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Set, Tuple

from django.utils.translation import gettext as _

from .refs import each_array, parse_ref
from .resource_loader import SkillResourceUnavailableError

if TYPE_CHECKING:
    from .declaration import SkillDeclaration, SkillOrchestration, SkillStep
    from .resource_loader import ResourceProvider, SkillResource
    from .schema_converter import ResourceParam

ResourceKey = Tuple[str, str, str]


@dataclass(frozen=True)
class MissingResource:
    gateway: str
    stage: str
    resource: str
    reason: str


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_resources: List[MissingResource] = field(default_factory=list)


def load_resources(
    orchestration: SkillOrchestration, provider: ResourceProvider
) -> Tuple[Dict[ResourceKey, Optional[SkillResource]], List[MissingResource]]:
    """按步骤顺序查询编排用到的资源，每个资源只查一次；不可编排的资源记为 None，原因放进 missing

    例如：三步都用 bk-sops 的 prod，其中 get_task_status 用了两次 -> 查询两个资源；
    prod 未发布 -> 两个资源都为 None，missing 里两条原因都是「环境 prod 未发布」
    """
    resources: Dict[ResourceKey, Optional[SkillResource]] = {}
    missing: List[MissingResource] = []
    for step in orchestration.steps:
        if step.key in resources:
            continue
        try:
            resources[step.key] = provider.get_resource(*step.key)
        except SkillResourceUnavailableError as err:
            resources[step.key] = None
            missing.append(MissingResource(*step.key, reason=str(err)))
    return resources, missing


def validate_declaration(declaration: SkillDeclaration, provider: ResourceProvider) -> ValidationResult:
    """对照资源定义校验声明；不可编排的资源放进 missing_resources，不算 error 也不算 warning，涉及它的字段级检查跳过

    例如：
        with 里的参数 foo 不在资源定义中 -> errors 有「<步骤 id>：参数 foo 不在资源定义中」
        资源未公开 -> warnings 有一条，errors 为空
    """
    result = ValidationResult()
    resources, result.missing_resources = load_resources(declaration.orchestration, provider)
    for resource in resources.values():
        if resource is not None:
            result.errors += resource.errors
            result.warnings += resource.warnings

    _RefChecker(declaration.orchestration, resources, result).check()
    return result


class _RefChecker:
    """按步骤顺序检查引用：只能引用已有输入和之前的步骤，引用到的响应字段要在资源定义里"""

    def __init__(
        self,
        orchestration: SkillOrchestration,
        resources: Dict[ResourceKey, Optional[SkillResource]],
        result: ValidationResult,
    ):
        self.orchestration = orchestration
        self.resources = resources
        self.result = result
        self.step_resources: Dict[str, Optional[SkillResource]] = {}
        # with 里有逐个调用参数的步骤，结果是多次调用的汇总
        self.each_steps: Set[str] = set()

    def check(self) -> None:
        """依次检查每步 with 的引用和参数、输出的引用，最后比对输入、输出的类型；问题写进 result.errors"""
        for step in self.orchestration.steps:
            for name, value in step.with_.items():
                self._check_ref(value, f"{step.id}.with.{name}")
            resource = self.resources[step.key]
            if resource and not resource.errors:
                self._check_params(step, resource)
            self.step_resources[step.id] = resource

        for name, output in self.orchestration.outputs.items():
            self._check_ref(output.value, f"outputs.{name}")
        self._check_input_types()
        self._check_output_types()

    def _check_ref(self, value: Any, where: str) -> None:
        """引用的输入要存在，引用的步骤要在当前步骤之前，引用的响应字段要在该步骤资源的定义里

        例如：
            "${{ inputs.biz }}"，没有输入 biz -> error「<where>：输入 biz 不存在」
            第 1 步引用 "${{ steps.wait.outputs.data }}"，wait 是第 2 步 -> error「引用的步骤 wait 不在当前步骤之前」
            固定值 -> 不检查
        """
        parsed = parse_ref(value)
        if parsed.kind == "input" and self.orchestration.get_input(parsed.name) is None:
            self.result.errors.append(_("{where}：输入 {name} 不存在").format(where=where, name=parsed.name))
        elif parsed.kind == "step":
            if parsed.step not in self.step_resources:
                self.result.errors.append(
                    _("{where}：引用的步骤 {step} 不在当前步骤之前").format(where=where, step=parsed.step)
                )
                return
            resource = self.step_resources[parsed.step]
            # 资源不存在，或资源定义本身已报 error 时，不再把每个字段都报成缺失
            if resource and not resource.errors and not resource.has_response_field(parsed.path):
                self.result.errors.append(
                    _("{where}：{resource} 的响应定义中没有 {path}").format(
                        where=where, resource=resource.data.name, path=parsed.path
                    )
                )

    def _check_params(self, step: SkillStep, resource: SkillResource) -> None:
        """必填参数和路径参数都要写进 with；逐个调用时每次不同的取值写成带 `[]` 的步骤引用，筛选条件写在步骤说明里

        例如：
            path 参数 task_id 没写进 with -> error「资源定义中必填的参数没有写进 with：task_id」
            必填参数取自选填且没有默认值的输入 -> error
            一步里两个参数分别取自 data[].id 和 items[].id -> error「逐个调用的参数须取自同一个数组」
        """
        missing = [
            param.name
            for param in resource.params
            if (param.required or param.location == "path") and param.name not in step.with_
        ]
        if missing:
            self.result.errors.append(
                _("{step}：资源定义中必填的参数没有写进 with：{params}").format(
                    step=step.id, params=", ".join(missing)
                )
            )

        arrays: Set[str] = set()
        for name, value in step.with_.items():
            param = resource.get_param(name)
            # 不在定义中的参数没有位置和类型，渲染只能靠猜，而版本写入后不能改
            if param is None:
                self.result.errors.append(_("{step}：参数 {name} 不在资源定义中").format(step=step.id, name=name))
                continue
            array = each_array(value, param.type)
            if array:
                arrays.add(array)
            parsed = parse_ref(value)
            if parsed.kind != "input":
                continue
            item = self.orchestration.get_input(parsed.name)
            if item and (param.required or param.location == "path") and item.omit_if_unset:
                self.result.errors.append(
                    _("{step}.with.{name}：参数 {name} 在资源定义中必填，输入 {input} 却是选填且没有默认值").format(
                        step=step.id, name=name, input=parsed.name
                    )
                )
        if arrays:
            self.each_steps.add(step.id)
        # 每次调用取同一个元素的各个字段，数组不同就说不清第几次调用取哪个元素
        if len(arrays) > 1:
            self.result.errors.append(
                _("{step}：逐个调用的参数须取自同一个数组：{arrays}").format(
                    step=step.id, arrays=", ".join(sorted(arrays))
                )
            )

    def _check_input_types(self) -> None:
        """输入声明的类型须与每个绑定参数的类型相同；定义里没写类型的参数不参与比较

        例如：输入 bk_biz_id 声明为 string，绑定的参数在定义中是 integer -> error
        """
        resources = {key: resource for key, resource in self.resources.items() if resource and not resource.errors}
        for name, bindings in input_bindings(self.orchestration, resources).items():
            declared = self.orchestration.inputs[name].type
            mismatched = [binding for binding in bindings if binding.param.type and binding.param.type != declared]
            if mismatched:
                detail = ", ".join(f"{item.step}.with.{item.param.name} ({item.param.type})" for item in mismatched)
                self.result.errors.append(
                    _("inputs.{name}：类型 {type} 与绑定参数不一致：{detail}").format(
                        name=name, type=declared, detail=detail
                    )
                )

    def _check_output_types(self) -> None:
        """输出声明的类型须与来源推出的类型相同；推不出（来源字段没写类型、资源缺失或有 error）时不比较

        例如：输出取自 integer 字段 data.task_id 却声明为 string -> error「类型 string 与来源不一致，应为 integer」
        """
        for name, output in self.orchestration.outputs.items():
            expected = self._source_type(output.value)
            if expected and expected != output.type:
                self.result.errors.append(
                    _("outputs.{name}：类型 {type} 与来源不一致，应为 {expected}").format(
                        name=name, type=output.type, expected=expected
                    )
                )

    def _source_type(self, value: Any) -> str:
        """取自输入时为输入类型；取自响应时为字段类型，路径里每个 `[]` 和逐个调用的来源步骤各包一层 array

        例如：
            "${{ inputs.bk_biz_id }}"，输入类型 integer -> "integer"
            "${{ steps.list.outputs.data[].id }}"，id 为 integer -> "array<integer>"
            "${{ steps.logs.outputs.data }}"，logs 是逐个调用、data 为 object -> "array<object>"
            来源字段没写类型 -> ""
        """
        parsed = parse_ref(value)
        if parsed.kind == "input":
            item = self.orchestration.get_input(parsed.name)
            return item.type if item else ""
        resource = self.step_resources.get(parsed.step)
        if parsed.kind != "step" or resource is None or resource.errors:
            return ""
        type_text = resource.response_type(parsed.path)
        if not type_text:
            return ""
        depth = parsed.path.count("[]") + (1 if parsed.step in self.each_steps else 0)
        for _index in range(depth):
            type_text = f"array<{type_text}>"
        return type_text


@dataclass(frozen=True)
class InputBinding:
    step: str
    param: ResourceParam


def input_bindings(
    orchestration: SkillOrchestration, resources: Mapping[ResourceKey, Optional[SkillResource]]
) -> Dict[str, List[InputBinding]]:
    """每个输入按步骤顺序绑定到的资源参数；资源或参数不存在的绑定不算

    例如：输入 job_instance_id 被第 2、3 步的 with 引用 ->
        {"job_instance_id": [InputBinding(step="wait", param=...), InputBinding(step="logs", param=...)]}；
        没被引用的输入对应空列表
    """
    bindings: Dict[str, List[InputBinding]] = {name: [] for name in orchestration.inputs}
    for step in orchestration.steps:
        resource = resources.get(step.key)
        if resource is None:
            continue
        for name, value in step.with_.items():
            parsed = parse_ref(value)
            param = resource.get_param(name)
            if parsed.kind == "input" and param and parsed.name in bindings:
                bindings[parsed.name].append(InputBinding(step=step.id, param=param))
    return bindings
