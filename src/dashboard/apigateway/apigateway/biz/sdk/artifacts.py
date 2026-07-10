"""Immutable SDK artifact and manifest metadata."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from django.conf import settings

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class BuiltArtifact:
    artifact_type: str
    path: Path
    filename: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ManifestFile:
    artifact_type: str
    filename: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ArtifactManifest:
    gateway_name: str
    resource_version: str
    language: str
    package_version: str
    input_fingerprint: str
    tool_versions: dict[str, str]
    files: tuple[ManifestFile, ...]

    def __post_init__(self):
        object.__setattr__(self, "tool_versions", MappingProxyType(dict(self.tool_versions)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "gateway_name": self.gateway_name,
            "resource_version": self.resource_version,
            "language": self.language,
            "package_version": self.package_version,
            "input_fingerprint": self.input_fingerprint,
            "tool_versions": dict(self.tool_versions),
            "files": [asdict(file) for file in self.files],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def create_built_artifact(
    artifact_type: str,
    path: Path,
    *,
    allowed_roots: tuple[Path, ...],
    max_size: int | None = None,
) -> BuiltArtifact:
    candidate = path.absolute()
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"invalid SDK artifact path: {path}")

    resolved = path.resolve(strict=True)
    if not any(resolved.is_relative_to(root.resolve(strict=True)) for root in allowed_roots):
        raise ValueError(f"SDK artifact escapes its build directory: {path}")
    if candidate != resolved:
        raise ValueError(f"SDK artifact path contains a symlink: {path}")

    size = resolved.stat().st_size
    limit = max_size or settings.SDK_GENERATION["max_artifact_bytes"]
    if size > limit:
        raise ValueError(f"SDK artifact exceeds the configured size limit: {path.name}")

    digest = hashlib.sha256()
    with resolved.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return BuiltArtifact(artifact_type, resolved, resolved.name, size, digest.hexdigest())


def validate_artifact_names(artifacts: list[BuiltArtifact]) -> None:
    folded = [artifact.filename.casefold() for artifact in artifacts]
    if len(folded) != len(set(folded)):
        raise ValueError("SDK artifact filenames must be unique ignoring case")


def build_manifest(
    gateway_name: str,
    resource_version: str,
    language: str,
    package_version: str,
    input_fingerprint: str,
    tool_versions: dict[str, str],
    artifacts: list[BuiltArtifact],
) -> ArtifactManifest:
    validate_artifact_names(artifacts)
    files = tuple(
        ManifestFile(item.artifact_type, item.filename, item.size, item.sha256)
        for item in sorted(artifacts, key=lambda artifact: artifact.filename)
    )
    return ArtifactManifest(
        gateway_name=gateway_name,
        resource_version=resource_version,
        language=language,
        package_version=package_version,
        input_fingerprint=input_fingerprint,
        tool_versions=dict(sorted(tool_versions.items())),
        files=files,
    )
