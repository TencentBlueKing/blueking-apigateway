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
"""Safe subprocess boundary for the pinned OpenAPI Generator CLI."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from django.conf import settings

from apigateway.biz.sdk.config import SDK_OPENAPI_GENERATOR_JAR
from apigateway.biz.sdk.exceptions import SDKGenerationError
from apigateway.biz.sdk.process import build_subprocess_env, redact_sensitive_text
from apigateway.biz.sdk.runtime import apply_runtime_requirements

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.config import SDKLanguageConfig


def _validate_output(output_dir: Path) -> None:
    if not output_dir.is_dir():
        raise SDKGenerationError("generator_failed", "OpenAPI Generator did not create an output directory")
    size = 0
    for path in output_dir.rglob("*"):
        if path.is_symlink():
            raise SDKGenerationError("generator_failed", "OpenAPI Generator output contains a symlink")
        if path.is_file():
            size += path.stat().st_size
            if size > settings.SDK_MAX_OUTPUT_BYTES:
                raise SDKGenerationError(
                    "generator_failed", "OpenAPI Generator output exceeds the configured size limit"
                )


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            shell=False,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=build_subprocess_env(),
            timeout=settings.SDK_SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise SDKGenerationError("generator_failed", "OpenAPI Generator timed out", retryable=True) from error


def generate_client(spec_path: Path, output_dir: Path, config: SDKLanguageConfig) -> None:
    if not spec_path.is_file():
        raise SDKGenerationError("generator_failed", "OpenAPI input file does not exist")

    additional_properties = ",".join(f"{key}={value}" for key, value in sorted(config.additional_properties.items()))
    command = [
        "java",
        "-jar",
        SDK_OPENAPI_GENERATOR_JAR,
        "generate",
        "-i",
        str(spec_path),
        "-g",
        config.generator_name,
        "-o",
        str(output_dir),
        "--additional-properties",
        additional_properties,
        "--global-property",
        "apiTests=false,modelTests=false",
    ]
    result = _run(command)
    if result.returncode != 0:
        stderr = redact_sensitive_text(" ".join((result.stderr or "").split()))[:768]
        detail = f": {stderr}" if stderr else ""
        raise SDKGenerationError(
            "generator_failed",
            f"OpenAPI Generator exited with status {result.returncode}{detail}",
        )
    _validate_output(output_dir)
    apply_runtime_requirements(config.language, output_dir)
    _validate_output(output_dir)
