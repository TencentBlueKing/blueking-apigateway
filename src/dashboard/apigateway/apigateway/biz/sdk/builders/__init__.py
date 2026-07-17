from __future__ import annotations

from typing import TYPE_CHECKING

from . import go, java, javascript, python, rust

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact
    from apigateway.biz.sdk.config import SDKLanguageConfig


def build_artifacts(
    language: str,
    source_dir: Path,
    output_dir: Path,
    config: SDKLanguageConfig,
) -> list[BuiltArtifact]:
    if language != config.language:
        raise ValueError("SDK builder language does not match its configuration")
    if language == "python":
        return python.build(source_dir, output_dir)
    if language == "java":
        return java.build(source_dir, output_dir)
    if language == "go":
        return go.build(source_dir, output_dir, config)
    if language == "javascript":
        return javascript.build(source_dir, output_dir)
    if language == "rust":
        return rust.build(source_dir, output_dir)
    raise ValueError(f"unsupported SDK builder language: {language}")


__all__ = ["build_artifacts"]
