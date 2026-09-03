from __future__ import annotations

import configparser
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from apigateway.common.pypi.registry import SimplePypiRegistry
from apigateway.utils.pypi import RepositoryConfig

from .common import PublishedArtifact, remote_sha256, require_matching_remote, run_publisher

if TYPE_CHECKING:
    from apigateway.biz.sdk.artifacts import BuiltArtifact
    from apigateway.biz.sdk.config import SDKLanguageConfig


def _repository_credentials_for_url(repository: RepositoryConfig, url: str) -> tuple[str, str]:
    index = urlsplit(repository.index_url)
    target = urlsplit(url)
    default_ports = {"http": 80, "https": 443}
    index_origin = (index.scheme.lower(), index.hostname, index.port or default_ports.get(index.scheme.lower()))
    target_origin = (target.scheme.lower(), target.hostname, target.port or default_ports.get(target.scheme.lower()))
    if index_origin != target_origin:
        return "", ""
    return repository.username, repository.password


def publish(artifacts: list[BuiltArtifact], config: SDKLanguageConfig) -> list[PublishedArtifact]:
    repository = RepositoryConfig.by_name("default")
    if not repository.repository_url:
        return []

    publishable = [artifact for artifact in artifacts if artifact.artifact_type in {"wheel", "sdist"}]
    if {artifact.artifact_type for artifact in publishable} != {"wheel", "sdist"}:
        raise ValueError("PyPI publication requires a wheel and sdist")

    registry = SimplePypiRegistry(
        repository.index_url,
        auth=(repository.username, repository.password) if repository.username or repository.password else None,
    )
    missing = []
    results = []
    package_types = {"wheel": "bdist_wheel", "sdist": "sdist"}
    for artifact in publishable:
        package = registry.search(config.project_name, config.package_version, package_types[artifact.artifact_type])
        if package is None:
            missing.append(artifact)
            continue
        username, password = _repository_credentials_for_url(repository, package.url)
        remote = remote_sha256(package.url, username=username, password=password)
        if remote is None:
            missing.append(artifact)
            continue
        require_matching_remote(package.url, remote, artifact.sha256, artifact.size)
        results.append(
            PublishedArtifact(
                "pypi",
                artifact.artifact_type,
                artifact.filename,
                f"{config.project_name}=={config.package_version}",
                package.url,
                artifact.size,
                artifact.sha256,
            )
        )

    if missing:
        with tempfile.TemporaryDirectory(prefix="sdk-pypi-") as directory:
            config_path = Path(directory) / ".pypirc"
            parser = configparser.ConfigParser(interpolation=None)
            parser["distutils"] = {"index-servers": "default"}
            parser["default"] = {
                "repository": repository.repository_url,
                "username": repository.username,
                "password": repository.password,
            }
            with config_path.open("w") as file:
                parser.write(file)
            config_path.chmod(0o600)
            env = os.environ.copy()
            env["HOME"] = directory
            run_publisher(
                [
                    "twine",
                    "upload",
                    "--repository",
                    "default",
                    "--config-file",
                    str(config_path),
                    *[str(artifact.path) for artifact in missing],
                ],
                cwd=Path(directory),
                env=env,
                sensitive_values=(repository.username, repository.password),
            )
        for artifact in missing:
            package = registry.search(
                config.project_name, config.package_version, package_types[artifact.artifact_type]
            )
            if package is None:
                raise ValueError(f"PyPI artifact is unavailable after upload: {artifact.filename}")
            username, password = _repository_credentials_for_url(repository, package.url)
            remote = remote_sha256(package.url, username=username, password=password)
            if remote is None:
                raise ValueError(f"PyPI artifact is unavailable after upload: {artifact.filename}")
            require_matching_remote(package.url, remote, artifact.sha256, artifact.size)
            results.append(
                PublishedArtifact(
                    "pypi",
                    artifact.artifact_type,
                    artifact.filename,
                    f"{config.project_name}=={config.package_version}",
                    package.url,
                    artifact.size,
                    artifact.sha256,
                )
            )
    return sorted(results, key=lambda artifact: artifact.filename)
