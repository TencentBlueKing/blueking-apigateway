"""Shared safety helpers for ecosystem builders."""

from __future__ import annotations

import subprocess
import zipfile
from typing import TYPE_CHECKING

from django.conf import settings

from apigateway.biz.sdk.artifacts import BuiltArtifact, create_built_artifact, validate_artifact_names
from apigateway.biz.sdk.exceptions import SDKGenerateError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def run_build(command: list[str], *, cwd: Path, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=False,
            check=False,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            text=True,
            timeout=settings.SDK_GENERATION["subprocess_timeout_seconds"],
        )
    except subprocess.TimeoutExpired as error:
        raise SDKGenerateError("build_failed", "SDK package build timed out") from error
    if result.returncode != 0:
        raise SDKGenerateError("build_failed", f"SDK package build exited with status {result.returncode}")
    return result


def collect_artifacts(entries: Iterable[tuple[str, Path]], source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    artifacts = [create_built_artifact(kind, path, allowed_roots=(source_dir, output_dir)) for kind, path in entries]
    validate_artifact_names(artifacts)
    return artifacts


def write_deterministic_zip(destination: Path, entries: Iterable[tuple[str, Path]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for archive_name, path in sorted(entries):
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"invalid SDK source file: {path}")
            info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
