"""Safe subprocess boundary for the pinned OpenAPI Generator CLI."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from django.conf import settings

from apigateway.biz.sdk.exceptions import SDKGenerateError

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.config import SDKLanguageConfig


def _run(command: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            shell=False,
            check=False,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            text=True,
            timeout=settings.SDK_GENERATION["subprocess_timeout_seconds"],
        )
    except subprocess.TimeoutExpired as error:
        raise SDKGenerateError("generator_failed", "OpenAPI Generator timed out") from error


def generate_client(spec_path: Path, output_dir: Path, config: SDKLanguageConfig) -> None:
    if not spec_path.is_file():
        raise SDKGenerateError("generator_failed", "OpenAPI input file does not exist")

    additional_properties = ",".join(f"{key}={value}" for key, value in sorted(config.additional_properties.items()))
    command = [
        "java",
        "-jar",
        settings.SDK_GENERATION["generator_jar"],
        "generate",
        "-i",
        str(spec_path),
        "-g",
        config.generator_name,
        "-o",
        str(output_dir),
        "--additional-properties",
        additional_properties,
    ]
    result = _run(command)
    if result.returncode != 0:
        raise SDKGenerateError(
            "generator_failed",
            f"OpenAPI Generator exited with status {result.returncode}",
        )


def get_openapi_generator_version() -> str:
    command = ["java", "-jar", settings.SDK_GENERATION["generator_jar"], "version"]
    result = _run(command, capture_output=True)
    if result.returncode != 0:
        raise SDKGenerateError(
            "generator_failed",
            f"OpenAPI Generator version probe exited with status {result.returncode}",
        )

    actual = result.stdout.strip()
    expected = settings.SDK_GENERATION["generator_version"]
    if actual != expected:
        raise SDKGenerateError(
            "generator_failed",
            f"OpenAPI Generator version mismatch: expected {expected}, got {actual or 'empty output'}",
        )
    return actual
