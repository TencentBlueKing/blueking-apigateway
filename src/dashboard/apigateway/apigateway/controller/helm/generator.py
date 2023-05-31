#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import re
import textwrap
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from blue_krill.cubing_case import shortcuts
from pydantic import BaseModel
from pydantic.fields import ModelField

from apigateway.utils.archivefile import TgzArchiveFile
from apigateway.utils.dict import get_item_by_path, set_item_by_path
from apigateway.utils.file import iter_files_recursive
from apigateway.utils.template import TemplatedStructureGenerator
from apigateway.utils.yaml import yaml_dumps, yaml_loads

EXTRA_ATTR_HELM_VALUE = "helm_value"
EXTRA_ATTR_HELM_VALUE_DEFAULT = "helm_value_default"
EXTRA_ATTR_HELM_VALUE_DEFAULT_SAFE = "helm_value_default_safe"


class ContextFieldCompiled(BaseModel):
    """用于保存编译后的字段信息"""

    paths: List[str]
    field: ModelField
    raw_value: Any

    class Config:
        arbitrary_types_allowed = True


class ContextCompiler:
    def __init__(self, context: BaseModel):  # noqa
        self._context = context
        # 经过 yaml 转化后的结构
        self._compiled_context = yaml_loads(yaml_dumps(context.dict(by_alias=True)))
        # values 需处理的字段
        self._compiled_value_fields: List[ContextFieldCompiled] = []
        # 子模型对应的字段
        self._compiled_model_fields: Dict[int, ContextFieldCompiled] = {}

        model_stack = cast(List[Tuple[List[str], BaseModel]], deque([([], context)]))

        def iter_mappings(paths: List[str], value: Dict[str, Any]):
            for k, v in value.items():
                if isinstance(v, BaseModel):
                    yield paths + [k], v

                if isinstance(v, dict):
                    yield from iter_mappings(paths + [k], v)

        while model_stack:
            current_paths, current_model = model_stack.pop()

            for attr, field in current_model.__fields__.items():
                # 私有字段
                if attr.startswith("_"):
                    continue

                key = field.alias
                value = getattr(current_model, attr)
                field_info = field.field_info
                if not field_info:
                    continue

                paths = current_paths + [key]
                # FIXME: 标志这个字段用于 helm values，应该以一种更好维护的方式提供
                # model 难以处理默认值，暂不支持
                if field_info.extra.get(EXTRA_ATTR_HELM_VALUE, False):
                    self._compiled_value_fields.append(
                        ContextFieldCompiled(
                            paths=paths,
                            field=field,
                            raw_value=value,
                        )
                    )

                # 判断是否需要嵌套分析，因列表在 helm values 中处理有困难，因此不支持
                if isinstance(value, BaseModel):
                    model_stack.append((paths, value))
                    self._compiled_model_fields[id(value)] = ContextFieldCompiled(
                        paths=paths,
                        field=field,
                        raw_value=value,
                    )

                if not isinstance(value, dict):
                    continue

                for p, m in iter_mappings(paths, value):
                    model_stack.append((p, m))
                    self._compiled_model_fields[id(m)] = ContextFieldCompiled(
                        paths=p,
                        field=field,
                        raw_value=m,
                    )

    def get_values_context(
        self, default_only: bool = False, path_prefixes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """获取实际生效的 helm values"""

        result: Dict[str, Any] = {}
        path_prefixes = path_prefixes or []

        for f in self._compiled_value_fields:
            field_info = f.field.field_info

            if not default_only or field_info.extra.get(EXTRA_ATTR_HELM_VALUE_DEFAULT_SAFE, False):
                value = get_item_by_path(self._compiled_context, f.paths)
            elif EXTRA_ATTR_HELM_VALUE_DEFAULT in field_info.extra:
                value = field_info.extra[EXTRA_ATTR_HELM_VALUE_DEFAULT]
            else:
                # 获取默认值，作为 chart 内置 values
                value = f.field.get_default()

            set_item_by_path(result, [shortcuts.to_lower_camel_case(i) for i in path_prefixes + f.paths], value)

        return result

    def get_chart_context(
        self, values_prefix: str = ".Values", by: Optional[BaseModel] = None, indent_step: int = 2
    ) -> Dict[str, Any]:
        """获取 chart 模板，自动引用对应的 values 值"""

        if by:
            field = self._compiled_model_fields[id(by)]
            result = deepcopy(get_item_by_path(self._compiled_context, field.paths))
            value_path_prefix = field.paths
        else:
            result = deepcopy(self._compiled_context)
            value_path_prefix = []

        value_path_prefix_length = len(value_path_prefix)
        for f in self._compiled_value_fields:
            if f.paths[:value_path_prefix_length] != value_path_prefix:
                continue

            parts = [f"{values_prefix}.{'.'.join(map(shortcuts.to_lower_camel_case, f.paths))}", "toYaml"]

            # 复杂对象需要换行缩进
            if f.field.is_complex():
                parts.append(f"nindent {indent_step * len(f.paths[value_path_prefix_length:])}")

            set_item_by_path(
                result,
                f.paths[value_path_prefix_length:],
                "{{ %s }}" % " | ".join(parts),
            )

        return result


class CrdChartGenerator:
    """CRD模板生成器"""

    def __init__(self, template_dir: str, context: BaseModel):
        self._generator = TemplatedStructureGenerator(
            template_dir=template_dir,
            template_environment_attrs={
                "variable_start_string": "{$",
                "variable_end_string": "$}",
            },
        )
        self._context = context
        self._context_compiler = ContextCompiler(context)
        self._chart_template_ref_regex = re.compile(r"'?{{\s*(.*?)\s*}}'?")
        self._chart_template_filter_regex = re.compile(r"\s*\|\s*")

        self._generator.register_filters(
            nindent=self._filter_nindent,
            crd_name=shortcuts.to_lower_dash_case,
            to_spec_yaml=self._filter_to_chart_context,
            to_values_yaml=self._filter_to_values_context,
        )

    def _filter_nindent(self, value, width):
        """添加缩进，并在字符串开始处添加换行符"""

        return f"\n{textwrap.indent(value, ' ' * width)}"

    def _filter_to_chart_context(self, value, prefix: str = ".Values", indent_level: int = 0, indent_step: int = 2):
        """转换为 chart 模型的上下文"""

        def fix_template_indent(template: str):
            fixed = []
            terms = self._chart_template_filter_regex.split(template)
            for term in terms:
                func, _, value = term.partition(" ")
                if func == "nindent":
                    term = f"nindent {int(value) + indent_level * indent_step}"
                fixed.append(term)

            return "{{ %s }}" % " | ".join(fixed)

        yaml = yaml_dumps(
            self._context_compiler.get_chart_context(
                by=value,
                values_prefix=prefix,
                indent_step=indent_step,
            )
        )
        result = []
        for line in yaml.splitlines():
            parts = []
            in_template = False
            for p in self._chart_template_ref_regex.split(line):
                if not in_template:
                    parts.append(p)
                else:
                    parts.append(fix_template_indent(p))

                in_template = not in_template
            result.append("".join(parts))

        return self._filter_nindent("\n".join(result), indent_level * indent_step)

    def _filter_to_values_context(self, value):
        """转换为 helm values 的上下文"""

        result = self._context_compiler.get_values_context(default_only=True)
        return yaml_dumps(result)

    def generate_values(self):
        """返回当前生效的 values"""
        return self._context_compiler.get_values_context()

    def generate_chart(self, output_dir: str):
        """生成模板并返回当前生效的 values"""

        self._generator.generate(output_dir, {"context": self._context})

    def generate(self, output_dir: str) -> str:
        output = Path(output_dir)
        chart_dir = output.joinpath("chart")
        chart_dir.mkdir(parents=True, exist_ok=True)
        self.generate_chart(str(chart_dir))

        archive = TgzArchiveFile()
        files = []
        for f in iter_files_recursive(chart_dir):
            files.append(f.relative_to(output_dir).as_posix())

        return archive.archive(str(output), "chart.tgz", files)
