from __future__ import annotations

import json
from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_build(
        ["npm", "pack", "--json", "--pack-destination", str(output_dir)],
        cwd=source_dir,
        capture_output=True,
    )
    try:
        payload = json.loads(result.stdout)
        filename = payload[0]["filename"]
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("npm pack returned invalid JSON output") from error
    return collect_artifacts([("npm_tgz", output_dir / filename)], source_dir, output_dir)
