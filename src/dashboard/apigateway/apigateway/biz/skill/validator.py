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
"""声明的完整校验：编排前后引用关系、资源定义不可用、参数不在资源定义中（error），以及其他与资源定义的对照（warning）。

结构和字段规则已在解析声明时检查，见 declaration.py。步骤的 if 和 description 是自然语言，不校验。
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .refs import parse_ref

if TYPE_CHECKING:
    from .declaration import SkillDeclaration, SkillOrchestration, SkillStep
    from .resource_definition import ResourceDefinition, ResourceProvider

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
    """按步骤顺序查询编排用到的资源，每个资源只查一次"""
    resources: Dict[ResourceKey, Optional[ResourceDefinition]] = {}
    for step in orchestration.steps:
        if step.key not in resources:
            resources[step.key] = provider.get_resource(*step.key)
    return resources


def validate_declaration(declaration: SkillDeclaration, provider: ResourceProvider) -> ValidationResult:
    """缺失的资源放进 missing_resources，不算 error 也不算 warning，涉及它的字段级检查跳过"""
    result = ValidationResult()
    resources = load_resources(declaration.orchestration, provider)
    for key, resource in resources.items():
        if resource is None:
            result.missing_resources.append(MissingResource(*key))
        else:
            result.errors += resource.errors
            result.warnings += resource.warnings

    _RefChecker(declaration.orchestration, resources, result).check()
    return result


class _RefChecker:
    """按步骤顺序检查引用：只能引用已有输入和之前的步骤，引用到的响应字段要在资源定义里"""

    def __init__(
        self,
        orchestration: SkillOrchestration,
        resources: Dict[ResourceKey, Optional[ResourceDefinition]],
        result: ValidationResult,
    ):
        self.orchestration = orchestration
        self.resources = resources
        self.result = result
        self.step_resources: Dict[str, Optional[ResourceDefinition]] = {}

    def check(self) -> None:
        for step in self.orchestration.steps:
            for name, value in step.with_.items():
                self._check_ref(value, f"{step.id}.with.{name}")
            resource = self.resources[step.key]
            if resource and not resource.errors:
                self._check_params(step, resource)
            self.step_resources[step.id] = resource

        for name, output in self.orchestration.outputs.items():
            self._check_ref(output.value, f"outputs.{name}")

    def _check_ref(self, value: Any, where: str) -> None:
        parsed = parse_ref(value)
        if parsed.kind == "input" and self.orchestration.get_input(parsed.name) is None:
            self.result.errors.append(f"{where}：输入 {parsed.name} 不存在")
        elif parsed.kind == "step":
            if parsed.step not in self.step_resources:
                self.result.errors.append(f"{where}：引用的步骤 {parsed.step} 不在当前步骤之前")
                return
            resource = self.step_resources[parsed.step]
            # 资源不存在，或资源定义本身已报 error 时，不再把每个字段都报成缺失
            if resource and not resource.errors and not resource.has_response_field(parsed.path):
                self.result.warnings.append(f"{where}：{resource.resource} 的响应定义中没有 {parsed.path}")

    def _check_params(self, step: SkillStep, resource: ResourceDefinition) -> None:
        """必填参数没有写进 with 不报：逐个调用等每次不同的取值由步骤说明交代，渲染时列出"""
        for name, value in step.with_.items():
            param = resource.get_param(name)
            # 不在定义中的参数没有位置和类型，渲染只能靠猜，而版本写入后不能改
            if param is None:
                self.result.errors.append(f"{step.id}：参数 {name} 不在资源定义中")
                continue
            parsed = parse_ref(value)
            if parsed.kind != "input" or param.location == "path":
                continue
            item = self.orchestration.get_input(parsed.name)
            if item and not (param.type == item.type or param.type.startswith(item.type + "<")):
                self.result.warnings.append(
                    f"{step.id}.with.{name}：输入类型 {item.type} 与参数类型 {param.type} 不一致"
                )
