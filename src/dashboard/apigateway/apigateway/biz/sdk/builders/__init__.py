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

from . import go, java, javascript, python

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact
    from apigateway.biz.sdk.config import SDKLanguageConfig


def build_artifacts(
    language: str,
    source_dir: Path,
    output_dir: Path,
    config: SDKLanguageConfig,
) -> list[BuiltArtifact]:
    if language != config.language:
        raise ValueError("SDK builder language does not match its configuration")
    if language == "python":
        return python.build(source_dir, output_dir)
    if language == "java":
        return java.build(source_dir, output_dir)
    if language == "go":
        return go.build(source_dir, output_dir, config)
    if language == "javascript":
        return javascript.build(source_dir, output_dir)
    raise ValueError(f"unsupported SDK builder language: {language}")


__all__ = ["build_artifacts"]
