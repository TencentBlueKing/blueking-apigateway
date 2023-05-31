# -*- coding: utf-8 -*-
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
import yaml
from django.core.serializers.pyyaml import DjangoSafeDumper
from django.test import TestCase

from apigateway.utils.yaml import (
    YamlRepresenterEnum,
    YamlRepresenterHookMixin,
    multiline_str_presenter,
    yaml_dumps,
    yaml_loads,
)


class TestYaml(TestCase):
    def test_yaml_loads(self):
        data = [
            {
                "content": "animal: pets",
                "expected": {
                    "animal": "pets",
                },
            },
            {
                "content": """
                    - Cat
                    - Dog
                    - Goldfish
                """,
                "expected": ["Cat", "Dog", "Goldfish"],
            },
            {
                "content": """
                    language:
                      - Go
                      - Python
                    websites:
                      YAML: yaml.org
                """,
                "expected": {
                    "language": ["Go", "Python"],
                    "websites": {"YAML": "yaml.org"},
                },
            },
        ]
        for test in data:
            result = yaml_loads(test["content"])
            self.assertEqual(result, test["expected"])

    def test_yaml_dumps(self):
        data = [
            {
                "data": {
                    "animal": "pets",
                },
                "expected": "animal: pets\n",
            },
            {
                "data": ["Cat", "Dog", "Goldfish"],
                "expected": "- Cat\n- Dog\n- Goldfish\n",
            },
            {
                "data": {
                    "language": ["Go", "Python"],
                    "websites": {"YAML": "yaml.org"},
                },
                "expected": """\
language:
- Go
- Python
websites:
  YAML: yaml.org
""",
            },
            {
                "data": {"not_bool": "y"},
                "expected": "not_bool: 'y'\n",
            },
        ]
        for test in data:
            result = yaml_dumps(test["data"])
            self.assertEqual(result, test["expected"])


class TestYamlRepresenterHookMixin:
    class T(int, YamlRepresenterHookMixin):
        @classmethod
        def yaml_representer(cls, dumper, data):
            return dumper.represent_str(str(data))

    def test_yaml_representer(self, faker):
        value = self.T(faker.random_number())
        result = yaml_dumps([value])
        data = yaml_loads(result)
        assert data == [str(value)]


class TestYamlRepresenterEnum:
    class IntEnum(int, YamlRepresenterEnum):
        A = 1
        B = 2

    class StrEnum(str, YamlRepresenterEnum):
        A = "1"
        B = "2"

    def test_int_enum(self):
        result = yaml_dumps([self.IntEnum.A, self.IntEnum.B])
        data = yaml_loads(result)
        assert data == [1, 2]

    def test_str_enum(self):
        result = yaml_dumps([self.StrEnum.A, self.StrEnum.B])
        data = yaml_loads(result)
        assert data == ["1", "2"]


def test_multiline_str_presenter():
    DjangoSafeDumper.add_representer(str, multiline_str_presenter)

    data = {"colors": "green"}
    result = yaml.dump(data, Dumper=DjangoSafeDumper)
    assert "|" not in result

    data = {"colors": "green\nblue"}
    result = yaml.dump(data, Dumper=DjangoSafeDumper)
    assert "|" in result
