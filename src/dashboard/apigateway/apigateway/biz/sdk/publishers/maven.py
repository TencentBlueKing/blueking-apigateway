from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from apigateway.biz.sdk.maven_settings import write_maven_settings
from apigateway.utils.maven import RepositoryConfig

from .common import (
    PublishedArtifact,
    find_artifacts,
    remote_sha256,
    require_matching_remote,
    run_publisher,
    upload_file,
)

if TYPE_CHECKING:
    from apigateway.biz.sdk.artifacts import BuiltArtifact
    from apigateway.biz.sdk.config import SDKLanguageConfig


def _artifact_urls(repository_url: str, group_id: str, artifact_id: str, version: str) -> dict[str, str]:
    prefix = f"{repository_url.rstrip('/')}/{group_id.replace('.', '/')}/{artifact_id}/{version}"
    return {
        "jar": f"{prefix}/{artifact_id}-{version}.jar",
        "pom": f"{prefix}/{artifact_id}-{version}.pom",
        "sources_jar": f"{prefix}/{artifact_id}-{version}-sources.jar",
    }


def publish(artifacts: list[BuiltArtifact], config: SDKLanguageConfig) -> list[PublishedArtifact]:
    repository = RepositoryConfig.by_name("default")
    if not repository.repository_url:
        return []

    required = find_artifacts(artifacts, {"jar", "pom", "sources_jar"})
    if set(required) != {"jar", "pom", "sources_jar"}:
        raise ValueError("Maven publication requires JAR, POM, and sources JAR")
    properties = config.additional_properties
    group_id = properties["groupId"]
    artifact_id = properties["artifactId"]
    version = properties["artifactVersion"]
    urls = _artifact_urls(repository.repository_url, group_id, artifact_id, version)

    existing = {}
    for artifact_type, artifact in required.items():
        remote = remote_sha256(
            urls[artifact_type],
            username=repository.username,
            password=repository.password,
            verify=not repository.ssl_insecure,
        )
        if remote is not None:
            require_matching_remote(urls[artifact_type], remote, artifact.sha256, artifact.size)
            existing[artifact_type] = remote
    if existing and len(existing) != len(required):
        for artifact_type in set(required).difference(existing):
            artifact = required[artifact_type]
            upload_file(
                artifact.path,
                urls[artifact_type],
                username=repository.username,
                password=repository.password,
                verify=not repository.ssl_insecure,
            )
            remote = remote_sha256(
                urls[artifact_type],
                username=repository.username,
                password=repository.password,
                verify=not repository.ssl_insecure,
            )
            if remote is None:
                raise ValueError(f"Maven artifact is unavailable after upload: {urls[artifact_type]}")
            require_matching_remote(urls[artifact_type], remote, artifact.sha256, artifact.size)

    if not existing:
        with tempfile.TemporaryDirectory(prefix="sdk-maven-") as directory:
            settings_path = Path(directory) / "settings.xml"
            write_maven_settings(settings_path, repository)
            command = [
                "mvn",
                "-B",
                "-s",
                str(settings_path),
                "deploy:deploy-file",
                f"-Dfile={required['jar'].path}",
                f"-DpomFile={required['pom'].path}",
                f"-Dsources={required['sources_jar'].path}",
                f"-DrepositoryId={repository.repository_id}",
                f"-Durl={repository.repository_url}",
            ]
            if repository.ssl_insecure:
                command.extend(["-Dmaven.wagon.http.ssl.insecure=true", "-Dmaven.wagon.http.ssl.allowall=true"])
            run_publisher(
                command,
                cwd=Path(directory),
                sensitive_values=(repository.username, repository.password),
            )

    coordinate = f"{group_id}:{artifact_id}:{version}"
    return [
        PublishedArtifact(
            "maven",
            artifact_type,
            artifact.filename,
            coordinate,
            urls[artifact_type],
            artifact.size,
            artifact.sha256,
        )
        for artifact_type, artifact in sorted(required.items())
    ]
