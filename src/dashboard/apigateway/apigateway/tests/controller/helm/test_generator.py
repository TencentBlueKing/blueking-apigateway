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
from pathlib import Path
from typing import Any, Dict

import pytest
from pydantic import BaseModel, Field

from apigateway.controller.helm.generator import ContextCompiler, CrdChartGenerator
from apigateway.utils.yaml import yaml_loads


class InnerModel(BaseModel):
    name: str = Field(default="")
    kind: str = Field(default="default")
    value: int = Field(default=0, helm_value=True)
    safe_value: int = Field(default=0, helm_value=True, helm_value_default_safe=True)
    values: Dict[str, Any] = Field(default_factory=dict, helm_value=True)

    class Config:
        arbitrary_types_allowed = True


class OuterModel(BaseModel):
    inner: InnerModel = Field()
    mappings: Dict[str, InnerModel] = Field()
    deeply_mappings: Dict[str, Dict[str, InnerModel]] = Field()

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture()
def context_model(faker):
    def fake_inner_factory():
        return InnerModel(
            name=faker.pystr(),
            kind=faker.pystr(),
            value=faker.pyint(),
            safe_value=faker.pyint(),
            # 不支持 Decimal，yaml 无法 dump 其值
            values=faker.pydict(value_types=["str", "int", "float", "date_time", "uri", "email"]),
        )

    return OuterModel(
        inner=fake_inner_factory(),
        mappings={"model": fake_inner_factory()},
        deeply_mappings={"model": {"deeply": fake_inner_factory()}},
    )


class TestContextCompiler:
    @pytest.fixture(autouse=True)
    def make_compiler(self, context_model):
        self.compiler = ContextCompiler(
            context=context_model,
        )

    def test_get_values_context(self, context_model):
        assert self.compiler.get_values_context() == {
            "inner": {
                "value": context_model.inner.value,
                "safeValue": context_model.inner.safe_value,
                "values": context_model.inner.values,
            },
            "mappings": {
                "model": {
                    "value": context_model.mappings["model"].value,
                    "safeValue": context_model.mappings["model"].safe_value,
                    "values": context_model.mappings["model"].values,
                }
            },
            "deeplyMappings": {
                "model": {
                    "deeply": {
                        "value": context_model.deeply_mappings["model"]["deeply"].value,
                        "safeValue": context_model.deeply_mappings["model"]["deeply"].safe_value,
                        "values": context_model.deeply_mappings["model"]["deeply"].values,
                    },
                }
            },
        }

    def test_get_values_context_with_default_only(self, context_model):
        assert self.compiler.get_values_context(default_only=True) == {
            "inner": {
                "value": 0,
                "safeValue": context_model.inner.safe_value,
                "values": {},
            },
            "mappings": {
                "model": {
                    "value": 0,
                    "safeValue": context_model.mappings["model"].safe_value,
                    "values": {},
                }
            },
            "deeplyMappings": {
                "model": {
                    "deeply": {
                        "value": 0,
                        "safeValue": context_model.deeply_mappings["model"]["deeply"].safe_value,
                        "values": {},
                    },
                }
            },
        }

    def test_get_values_context_with_path_prefixes(self, context_model):
        assert self.compiler.get_values_context(path_prefixes=["context"]) == {
            "context": {
                "inner": {
                    "value": context_model.inner.value,
                    "safeValue": context_model.inner.safe_value,
                    "values": context_model.inner.values,
                },
                "mappings": {
                    "model": {
                        "value": context_model.mappings["model"].value,
                        "safeValue": context_model.mappings["model"].safe_value,
                        "values": context_model.mappings["model"].values,
                    }
                },
                "deeplyMappings": {
                    "model": {
                        "deeply": {
                            "value": context_model.deeply_mappings["model"]["deeply"].value,
                            "safeValue": context_model.deeply_mappings["model"]["deeply"].safe_value,
                            "values": context_model.deeply_mappings["model"]["deeply"].values,
                        },
                    }
                },
            },
        }

    def test_get_chart_context(self, context_model):
        result = self.compiler.get_chart_context()
        assert result == {
            "inner": {
                "name": context_model.inner.name,
                "kind": context_model.inner.kind,
                "value": "{{ .Values.inner.value | toYaml }}",
                "safe_value": "{{ .Values.inner.safeValue | toYaml }}",
                "values": "{{ .Values.inner.values | toYaml | nindent 4 }}",
            },
            "mappings": {
                "model": {
                    "name": context_model.mappings["model"].name,
                    "kind": context_model.mappings["model"].kind,
                    "value": "{{ .Values.mappings.model.value | toYaml }}",
                    "safe_value": "{{ .Values.mappings.model.safeValue | toYaml }}",
                    "values": "{{ .Values.mappings.model.values | toYaml | nindent 6 }}",
                }
            },
            "deeply_mappings": {
                "model": {
                    "deeply": {
                        "name": context_model.deeply_mappings["model"]["deeply"].name,
                        "kind": context_model.deeply_mappings["model"]["deeply"].kind,
                        "value": "{{ .Values.deeplyMappings.model.deeply.value | toYaml }}",
                        "safe_value": "{{ .Values.deeplyMappings.model.deeply.safeValue | toYaml }}",
                        "values": "{{ .Values.deeplyMappings.model.deeply.values | toYaml | nindent 8 }}",
                    },
                }
            },
        }

    def test_get_chart_context_with_values_prefix(self, context_model):
        result = self.compiler.get_chart_context(values_prefix="$model")
        assert result == {
            "inner": {
                "name": context_model.inner.name,
                "kind": context_model.inner.kind,
                "value": "{{ $model.inner.value | toYaml }}",
                "safe_value": "{{ $model.inner.safeValue | toYaml }}",
                "values": "{{ $model.inner.values | toYaml | nindent 4 }}",
            },
            "mappings": {
                "model": {
                    "name": context_model.mappings["model"].name,
                    "kind": context_model.mappings["model"].kind,
                    "value": "{{ $model.mappings.model.value | toYaml }}",
                    "safe_value": "{{ $model.mappings.model.safeValue | toYaml }}",
                    "values": "{{ $model.mappings.model.values | toYaml | nindent 6 }}",
                }
            },
            "deeply_mappings": {
                "model": {
                    "deeply": {
                        "name": context_model.deeply_mappings["model"]["deeply"].name,
                        "kind": context_model.deeply_mappings["model"]["deeply"].kind,
                        "value": "{{ $model.deeplyMappings.model.deeply.value | toYaml }}",
                        "safe_value": "{{ $model.deeplyMappings.model.deeply.safeValue | toYaml }}",
                        "values": "{{ $model.deeplyMappings.model.deeply.values | toYaml | nindent 8 }}",
                    },
                }
            },
        }

    def test_get_chart_context_by_inner(self, context_model):
        result = self.compiler.get_chart_context(by=context_model.inner)
        assert result == {
            "name": context_model.inner.name,
            "kind": context_model.inner.kind,
            "value": "{{ .Values.inner.value | toYaml }}",
            "safe_value": "{{ .Values.inner.safeValue | toYaml }}",
            "values": "{{ .Values.inner.values | toYaml | nindent 2 }}",
        }

    def test_get_chart_context_by_mappings_model(self, context_model):
        result = self.compiler.get_chart_context(by=context_model.mappings["model"])
        assert result == {
            "name": context_model.mappings["model"].name,
            "kind": context_model.mappings["model"].kind,
            "value": "{{ .Values.mappings.model.value | toYaml }}",
            "safe_value": "{{ .Values.mappings.model.safeValue | toYaml }}",
            "values": "{{ .Values.mappings.model.values | toYaml | nindent 2 }}",
        }

    def test_get_chart_context_by_deeply_mappings_model(self, context_model):
        result = self.compiler.get_chart_context(by=context_model.deeply_mappings["model"]["deeply"])
        assert result == {
            "name": context_model.deeply_mappings["model"]["deeply"].name,
            "kind": context_model.deeply_mappings["model"]["deeply"].kind,
            "value": "{{ .Values.deeplyMappings.model.deeply.value | toYaml }}",
            "safe_value": "{{ .Values.deeplyMappings.model.deeply.safeValue | toYaml }}",
            "values": "{{ .Values.deeplyMappings.model.deeply.values | toYaml | nindent 2 }}",
        }


class TestCrdChartGenerator:
    @pytest.fixture
    def template_dir(self, tmpdir):
        template_dir = tmpdir.mkdir("templates")

        values_path = template_dir.join("values.yaml.j2")
        values_path.write_text(
            "context: {$ context | to_values_yaml | nindent(width=2) $}",
            encoding="utf-8",
        )

        inner_resource_path = template_dir.join("inner.yaml.j2")
        inner_resource_path.write_text(
            """
spec: {$ context.inner | to_spec_yaml(prefix='.Values.context') | nindent(width=2) $}
            """,
            encoding="utf-8",
        )

        mappings_resource_path = template_dir.join("mappings.yaml.j2")
        mappings_resource_path.write_text(
            """
spec: {$ context.mappings['model'] | to_spec_yaml(prefix='.Values.context') | nindent(width=2) $}
            """,
            encoding="utf-8",
        )

        deeply_mappings_resource_path = template_dir.join("deeply_mappings.yaml.j2")
        deeply_mappings_resource_path.write_text(
            """
spec: {$ context.deeply_mappings['model']['deeply'] | to_spec_yaml(prefix='.Values.context') | nindent(width=2) $}
            """,
            encoding="utf-8",
        )

        readme_path = template_dir.join("README.md")
        readme_path.write_text("", encoding="utf-8")

        return template_dir

    @pytest.fixture
    def output_dir(self, tmpdir):
        output_dir = tmpdir.mkdir("output")
        return output_dir

    @pytest.fixture(autouse=True)
    def make_generator(self, template_dir, output_dir, context_model):
        self.generator = CrdChartGenerator(template_dir, context_model)

    def test_generate_chart(self, context_model, output_dir):
        self.generator.generate_chart(output_dir)

        for f in ["README.md", "values.yaml", "inner.yaml", "mappings.yaml", "deeply_mappings.yaml"]:
            path = output_dir.join(f)
            assert path.exists()

            assert "'{{" not in path.read_text(encoding="utf-8")

        values = yaml_loads(output_dir.join("values.yaml").read_text(encoding="utf-8"))
        assert "context" in values

    def test_generate(self, context_model, output_dir):
        result = self.generator.generate(output_dir)

        assert Path(result).is_file()
