from __future__ import annotations

from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
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
