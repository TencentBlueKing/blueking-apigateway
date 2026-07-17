from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

import requests
from django.conf import settings

from apigateway.biz.sdk.exceptions import SDKArtifactConflict, SDKGenerateError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


@dataclass(frozen=True)
class PublishedArtifact:
    distributor: str
    artifact_type: str
    filename: str
    coordinate: str
    url: str
    size: int
    sha256: str


def remote_sha256(
    url: str,
    *,
    username: str,
    password: str,
    verify: bool = True,
) -> tuple[str, int] | None:
    response = requests.get(
        url,
        auth=(username, password) if username or password else None,
        timeout=settings.SDK_GENERATION["subprocess_timeout_seconds"],
        verify=verify,
        stream=True,
    )
    try:
        if response.status_code == 404:
            return None
        response.raise_for_status()
        digest = hashlib.sha256()
        size = 0
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                size += len(chunk)
                digest.update(chunk)
        return digest.hexdigest(), size
    finally:
        response.close()


def require_matching_remote(url: str, remote: tuple[str, int], expected_sha256: str, expected_size: int) -> None:
    if remote != (expected_sha256, expected_size):
        raise SDKArtifactConflict(f"native SDK artifact has different content: {url}")


def run_publisher(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=False,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=settings.SDK_GENERATION["subprocess_timeout_seconds"],
        )
    except subprocess.TimeoutExpired as error:
        raise SDKGenerateError("native_publish_failed", "native SDK publication timed out") from error
    if result.returncode != 0:
        raise SDKGenerateError(
            "native_publish_failed", f"native SDK publication exited with status {result.returncode}"
        )


def find_artifacts(artifacts: Iterable, artifact_types: set[str]):
    return {artifact.artifact_type: artifact for artifact in artifacts if artifact.artifact_type in artifact_types}
