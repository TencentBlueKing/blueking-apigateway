#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import ast
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[2] / "service"


def _assigns_dunder_all(module_path: Path) -> bool:
    tree = ast.parse(module_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                return True
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
            return True
    return False


def _service_package_dirs() -> list[Path]:
    return sorted(
        package_dir
        for package_dir in SERVICE_DIR.iterdir()
        if package_dir.is_dir()
        and (package_dir / "__init__.py").exists()
        and any(module_path.name != "__init__.py" for module_path in package_dir.glob("*.py"))
    )


def _service_leaf_modules() -> list[Path]:
    return sorted(
        module_path
        for package_dir in _service_package_dirs()
        for module_path in package_dir.glob("*.py")
        if module_path.name != "__init__.py"
    )


@pytest.mark.parametrize("package_dir", _service_package_dirs(), ids=lambda path: path.name)
def test_service_package_public_api_is_declared_in_init(package_dir):
    assert _assigns_dunder_all(package_dir / "__init__.py")


@pytest.mark.parametrize("module_path", _service_leaf_modules(), ids=lambda path: f"{path.parent.name}/{path.name}")
def test_service_leaf_modules_do_not_define_dunder_all(module_path):
    assert not _assigns_dunder_all(module_path)
