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
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import FileSystemLoader
from jinja2.environment import Environment


@dataclass
class TemplatedStructureGenerator:
    """
    This class is used to generate the structure from the template.
    """

    template_dir: str
    template_ext: str = ".j2"
    template_environment_attrs: dict = field(default_factory=dict)
    template_environment: Environment = field(init=False)

    def __post_init__(self):
        self.template_environment = Environment(
            loader=FileSystemLoader(self.template_dir),
            **self.template_environment_attrs,
        )

    def register_filters(self, **filters):
        """
        Register filters to the template environment.
        """
        self.template_environment.filters.update(filters)

    def register_functions(self, **functions):
        """
        Register functions to the template environment.
        """
        self.template_environment.globals.update(functions)

    def _generate_file_from_template(self, src: Path, dest: Path, context: dict) -> None:
        """
        Copy the file from the template dir.
        """
        template_name = str(src.relative_to(self.template_dir))
        template = self.template_environment.get_template(template_name)
        result = template.render(**context)

        new_path, _ = os.path.splitext(dest)
        with open(new_path, "w") as f:
            f.write(result)

    def generate(
        self,
        output_dir: str,
        context: dict,
    ) -> None:
        """
        Generate the structure from the template.
        """
        for root, dirs, files in os.walk(self.template_dir):
            root_dir = Path(root)
            target_dir = Path(output_dir).joinpath(root_dir.relative_to(self.template_dir))

            for dir_name in dirs:
                target_dir.joinpath(dir_name).mkdir(parents=True, exist_ok=True)

            for file in files:
                src = root_dir.joinpath(file)
                dest = target_dir.joinpath(file)
                if not file.endswith(self.template_ext):
                    shutil.copy(src, dest)
                else:
                    self._generate_file_from_template(src, dest, context)
