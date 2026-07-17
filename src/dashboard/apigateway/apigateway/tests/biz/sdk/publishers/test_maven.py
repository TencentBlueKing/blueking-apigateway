import subprocess

import pytest

from apigateway.biz.sdk.exceptions import SDKArtifactConflict
from apigateway.biz.sdk.publishers import publish_native


def maven_artifacts(factory):
    return [
        factory("jar", "demo.jar", b"jar"),
        factory("pom", "pom.xml", b"pom"),
        factory("sources_jar", "demo-sources.jar", b"sources"),
    ]


def test_maven_upload_uses_settings_file_and_expected_files(mocker, built_artifact, java_config, settings):
    settings.MAVEN_MIRRORS_CONFIG = {
        "default": {
            "repository_url": "https://repo/maven",
            "repository_id": "internal",
            "username": "user",
            "password": "secret",
        }
    }
    mocker.patch("apigateway.biz.sdk.publishers.maven.remote_sha256", return_value=None)
    run = mocker.patch(
        "apigateway.biz.sdk.publishers.common.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    )

    results = publish_native("java", maven_artifacts(built_artifact), java_config)

    command = run.call_args.args[0]
    assert command[:2] == ["mvn", "-B"]
    assert any(argument.startswith("-Dfile=") for argument in command)
    assert any(argument.startswith("-DpomFile=") for argument in command)
    assert any(argument.startswith("-Dsources=") for argument in command)
    assert "secret" not in " ".join(command)
    assert {result.artifact_type for result in results} == {"jar", "pom", "sources_jar"}


def test_maven_matching_remote_is_reused(mocker, built_artifact, java_config, settings):
    settings.MAVEN_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/maven", "repository_id": "internal"}}
    artifacts = maven_artifacts(built_artifact)
    mocker.patch(
        "apigateway.biz.sdk.publishers.maven.remote_sha256",
        side_effect=[(artifact.sha256, artifact.size) for artifact in artifacts],
    )
    run = mocker.patch("apigateway.biz.sdk.publishers.common.subprocess.run")

    assert len(publish_native("java", artifacts, java_config)) == 3
    run.assert_not_called()


def test_maven_remote_conflict_is_rejected(mocker, built_artifact, java_config, settings):
    settings.MAVEN_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/maven", "repository_id": "internal"}}
    artifacts = maven_artifacts(built_artifact)
    mocker.patch(
        "apigateway.biz.sdk.publishers.maven.remote_sha256",
        side_effect=[("bad", artifacts[0].size)],
    )

    with pytest.raises(SDKArtifactConflict):
        publish_native("java", artifacts, java_config)
