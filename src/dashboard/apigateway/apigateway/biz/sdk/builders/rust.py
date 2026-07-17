from __future__ import annotations

from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_dir = output_dir / "target"
    run_build(
        ["cargo", "package", "--allow-dirty", "--target-dir", str(target_dir)],
        cwd=source_dir,
    )
    crates = sorted((target_dir / "package").glob("*.crate"))
    if len(crates) != 1:
        raise ValueError("Rust SDK build must produce one crate")
    return collect_artifacts([("crate", crates[0])], source_dir, output_dir)
