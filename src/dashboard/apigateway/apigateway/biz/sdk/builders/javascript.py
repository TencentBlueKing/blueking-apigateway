from __future__ import annotations

import json
from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact


def _parse_pack_output(output: str) -> list[dict[str, str]]:
    lines = output.splitlines()
    json_start = next((index for index, line in enumerate(lines) if line.lstrip().startswith("[")), None)
    if json_start is None:
        raise ValueError("npm pack returned invalid JSON output")
    try:
        return json.loads("\n".join(lines[json_start:]))
    except json.JSONDecodeError as error:
        raise ValueError("npm pack returned invalid JSON output") from error


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_build(["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=source_dir)
    run_build(["npm", "run", "build", "--if-present"], cwd=source_dir)
    result = run_build(
        ["npm", "pack", "--ignore-scripts", "--json", "--pack-destination", str(output_dir)],
        cwd=source_dir,
        capture_output=True,
    )
    try:
        payload = _parse_pack_output(result.stdout)
        filename = payload[0]["filename"]
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError("npm pack returned invalid JSON output") from error
    return collect_artifacts([("npm_tgz", output_dir / filename)], source_dir, output_dir)
