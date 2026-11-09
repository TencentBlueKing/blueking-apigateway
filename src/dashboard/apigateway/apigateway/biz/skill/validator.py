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
"""声明的完整校验：编排前后引用关系（error），以及与资源定义的对照（warning）。

结构和字段规则已在解析声明时检查，见 declaration.py。
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from .constants import CREDENTIAL_PARAMS
from .declaration import SkillCall, SkillDeclaration, SkillOrchestration
from .refs import parse_ref, poll_expr_paths

if TYPE_CHECKING:
    from .resource_definition import ResourceDefinition, ResourceProvider

# 网关 Skill 的额外规则（只能调用所在网关、同一环境），返回 error 列表
GatewayRule = Callable[[SkillDeclaration], List[str]]
ResourceKey = Tuple[str, str, str]


@dataclass(frozen=True)
class MissingResource:
    gateway: str
    stage: str
    resource: str


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_resources: List[MissingResource] = field(default_factory=list)


def load_resources(
    orchestration: SkillOrchestration, provider: ResourceProvider
) -> Dict[ResourceKey, Optional[ResourceDefinition]]:
    """按调用顺序查询编排用到的资源，每个资源只查一次"""
    resources: Dict[ResourceKey, Optional[ResourceDefinition]] = {}
    for _, call in orchestration.iter_calls():
        if call.key not in resources:
            resources[call.key] = provider.get_resource(*call.key)
    return resources


def validate_declaration(
    declaration: SkillDeclaration,
    provider: ResourceProvider,
    *,
    gateway_rule: Optional[GatewayRule] = None,
) -> ValidationResult:
    """缺失的资源放进 missing_resources，不算 error 也不算 warning，涉及它的字段级检查跳过"""
    result = ValidationResult()
    if gateway_rule:
        result.errors += gateway_rule(declaration)

    resources = load_resources(declaration.orchestration, provider)
    for key, resource in resources.items():
        if resource is None:
            result.missing_resources.append(MissingResource(*key))
        else:
            result.warnings += resource.warnings

    _RefChecker(declaration.orchestration, resources, result).check()
    return result


class _RefChecker:
    """按调用顺序检查引用：只能引用已有输入和之前的调用，引用到的响应字段要在资源定义里"""

    def __init__(
        self,
        orchestration: SkillOrchestration,
        resources: Dict[ResourceKey, Optional[ResourceDefinition]],
        result: ValidationResult,
    ):
        self.orchestration = orchestration
        self.resources = resources
        self.result = result
        self.input_names = {item.name for item in orchestration.inputs}
        self.earlier_calls: List[Tuple[str, str]] = []
        self.call_resources: Dict[Tuple[str, str], Optional[ResourceDefinition]] = {}

    def check(self) -> None:
        for step, call in self.orchestration.iter_calls():
            where = f"{step.name}.{call.resource}"
            resource = self.resources[call.key]
            for_each_from = call.for_each.from_ if call.for_each else None
            if for_each_from:
                self._check_ref(for_each_from, f"{where}.for_each.from")
            for name, ref in call.params.items():
                self._check_ref(ref, f"{where}.params.{name}", for_each_from)
            if resource:
                self._check_params(call, resource, where)
                self._check_reads(call, resource, where)
                self._check_poll(call, resource, where)
            self.earlier_calls.append((step.name, call.resource))
            self.call_resources[(step.name, call.resource)] = resource

        for output in self.orchestration.outputs:
            self._check_ref(output.from_, f"outputs.{output.name}")

    def _check_ref(self, ref: Any, where: str, for_each_from: Optional[str] = None) -> None:
        parsed = parse_ref(ref)
        if parsed.kind == "input" and parsed.name not in self.input_names:
            self.result.errors.append(f"{where}：输入 {parsed.name} 不存在")
        elif parsed.kind == "each" and for_each_from:
            source = parse_ref(for_each_from)
            resource = self.call_resources.get((source.step, source.resource))
            full_path = f"{source.path}[].{parsed.path}"
            if resource and not resource.has_response_field(full_path):
                self.result.warnings.append(f"{where}：{source.resource} 的响应定义中没有 {full_path}")
        elif parsed.kind == "call":
            target = (parsed.step, parsed.resource)
            resource = self.call_resources.get(target)
            if target not in self.earlier_calls:
                self.result.errors.append(f"{where}：引用的调用 {parsed.step}.{parsed.resource} 不在当前调用之前")
            elif self.earlier_calls.count(target) > 1:
                self.result.errors.append(f"{where}：{parsed.resource} 在步骤 {parsed.step} 内出现多次，不能被引用")
            elif resource and not resource.has_response_field(parsed.path):
                self.result.warnings.append(f"{where}：{parsed.resource} 的响应定义中没有 {parsed.path}")

    def _check_params(self, call: SkillCall, resource: ResourceDefinition, where: str) -> None:
        for name, ref in call.params.items():
            param = resource.get_param(name)
            if param is None:
                self.result.warnings.append(f"{where}：参数 {name} 不在资源定义中")
                continue
            parsed = parse_ref(ref)
            if parsed.kind != "input" or param.location == "path":
                continue
            item = self.orchestration.get_input(parsed.name)
            if item and not (param.type == item.type or param.type.startswith(item.type + "<")):
                self.result.warnings.append(
                    f"{where}.params.{name}：输入类型 {item.type} 与参数类型 {param.type} 不一致"
                )

        for param in resource.params:
            if param.required and param.name not in call.params and param.name not in CREDENTIAL_PARAMS:
                self.result.warnings.append(f"{where}：必填参数 {param.name} 未映射，需在步骤说明中交代")

    def _check_reads(self, call: SkillCall, resource: ResourceDefinition, where: str) -> None:
        for path in call.reads:
            if not resource.has_response_field(path):
                self.result.warnings.append(f"{where}.reads：响应定义中没有 {path}")

    def _check_poll(self, call: SkillCall, resource: ResourceDefinition, where: str) -> None:
        if not call.poll:
            return
        for path in poll_expr_paths(call.poll.exprs):
            if not resource.has_response_field(path):
                self.result.warnings.append(f"{where}.poll：响应定义中没有 {path}")
