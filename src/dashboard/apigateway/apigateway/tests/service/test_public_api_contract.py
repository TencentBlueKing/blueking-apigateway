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
import ast
import tokenize
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[2] / "service"
PYTHON_SOURCE_DIR = SERVICE_DIR.parent


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


def _package_dunder_all(package_dir: Path) -> set[str]:
    tree = ast.parse((package_dir / "__init__.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue

        return {
            elt.value
            for elt in getattr(node.value, "elts", [])
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        }

    return set()


def _function_name_tokens(name: str) -> list[Path]:
    matched_paths = []
    for path in PYTHON_SOURCE_DIR.rglob("*.py"):
        with path.open("rb") as source_file:
            if any(
                token.string == name
                for token in tokenize.tokenize(source_file.readline)
                if token.type == tokenize.NAME
            ):
                matched_paths.append(path)

    return matched_paths


def _service_private_helper_violations() -> list[str]:
    violations = []

    for module_path in _service_leaf_modules():
        exported_names = _package_dunder_all(module_path.parent)
        tree = ast.parse(module_path.read_text())

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            if node.name.startswith("_") or node.name in exported_names:
                continue

            name_refs = [path for path in _function_name_tokens(node.name) if path != module_path]
            if not name_refs:
                violations.append(f"{module_path.relative_to(SERVICE_DIR.parent)}::{node.name}")

    return violations


@pytest.mark.parametrize("package_dir", _service_package_dirs(), ids=lambda path: path.name)
def test_service_package_public_api_is_declared_in_init(package_dir):
    assert _assigns_dunder_all(package_dir / "__init__.py")


@pytest.mark.parametrize("module_path", _service_leaf_modules(), ids=lambda path: f"{path.parent.name}/{path.name}")
def test_service_leaf_modules_do_not_define_dunder_all(module_path):
    assert not _assigns_dunder_all(module_path)


def test_service_private_helpers_are_prefixed_with_underscore():
    violations = _service_private_helper_violations()

    assert not violations, (
        "Module-private service helpers must be prefixed with '_' when they are not exported and have no callers "
        f"outside their defining module: {violations}"
    )


def test_plugin_compatibility_contract_is_public():
    exported_names = _package_dunder_all(SERVICE_DIR / "plugin")

    assert "AI_COMMON_PLUGIN_CODES" in exported_names
    assert "AI_ONLY_PLUGIN_CODES" in exported_names
    assert "is_plugin_compatible_with_resource_kind" in exported_names
