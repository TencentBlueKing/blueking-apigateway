from __future__ import annotations

from typing import TYPE_CHECKING

from . import maven, pypi
from .common import PublishedArtifact

if TYPE_CHECKING:
    from apigateway.biz.sdk.artifacts import BuiltArtifact
    from apigateway.biz.sdk.config import SDKLanguageConfig


def publish_native(
    language: str,
    artifacts: list[BuiltArtifact],
    language_config: SDKLanguageConfig,
) -> list[PublishedArtifact]:
    if language != language_config.language:
        raise ValueError("native publisher language does not match its configuration")
    if language_config.native_distributor is None:
        return []
    if language == "python" and language_config.native_distributor == "pypi":
        return pypi.publish(artifacts, language_config)
    if language == "java" and language_config.native_distributor == "maven":
        return maven.publish(artifacts, language_config)
    raise ValueError(f"unsupported native SDK publisher: {language_config.native_distributor}")


__all__ = ["PublishedArtifact", "publish_native"]
