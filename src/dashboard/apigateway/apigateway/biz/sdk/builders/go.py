from __future__ import annotations

import json
from typing import TYPE_CHECKING

from apigateway.biz.sdk.artifacts import BuiltArtifact, create_built_artifact, validate_artifact_names
from apigateway.biz.sdk.builders.common import run_build, write_deterministic_zip

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.config import SDKLanguageConfig

GO_PROXY_ZIP_LIMIT = 500 * 1024 * 1024


def build(source_dir: Path, output_dir: Path, config: SDKLanguageConfig) -> list[BuiltArtifact]:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_build(["go", "test", "./..."], cwd=source_dir)
    go_mod = source_dir / "go.mod"
    if not go_mod.is_file():
        raise ValueError("Go SDK build requires go.mod")

    basename = config.package_version
    info = output_dir / f"{basename}.info"
    mod = output_dir / f"{basename}.mod"
    module_zip = output_dir / f"{basename}.zip"
    info.write_text(json.dumps({"Version": config.package_version, "Time": "1970-01-01T00:00:00Z"}))
    mod.write_bytes(go_mod.read_bytes())

    prefix = f"{config.project_name}@{config.package_version}/"
    entries = []
    output_resolved = output_dir.resolve()
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.resolve().is_relative_to(output_resolved) or ".git" in path.parts:
            continue
        if path.is_symlink():
            raise ValueError(f"Go SDK source contains a symlink: {path}")
        entries.append((prefix + path.relative_to(source_dir).as_posix(), path))
    write_deterministic_zip(module_zip, entries)

    artifacts = [
        create_built_artifact("go_info", info, allowed_roots=(output_dir,)),
        create_built_artifact("go_mod", mod, allowed_roots=(output_dir,)),
        create_built_artifact("go_zip", module_zip, allowed_roots=(output_dir,), max_size=GO_PROXY_ZIP_LIMIT),
    ]
    validate_artifact_names(artifacts)
    return artifacts
