#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
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
from __future__ import annotations

from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build
from apigateway.biz.sdk.toolchain import prepare_generated_dependency_inputs

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    prepare_generated_dependency_inputs("python", source_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_build(
        ["python", "-m", "build", "--wheel", "--sdist", "--outdir", str(output_dir)],
        cwd=source_dir,
    )
    wheels = sorted(output_dir.glob("*.whl"))
    sdists = sorted(output_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("Python SDK build must produce one wheel and one sdist")
    return collect_artifacts([("wheel", wheels[0]), ("sdist", sdists[0])], source_dir, output_dir)
