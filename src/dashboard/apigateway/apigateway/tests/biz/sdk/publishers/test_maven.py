import subprocess

import pytest

from apigateway.biz.sdk.exceptions import SDKArtifactConflict, SDKGenerateError
from apigateway.biz.sdk.publishers import publish_native


def maven_artifacts(factory):
    return [
        factory("jar", "demo.jar", b"jar"),
        factory("pom", "pom.xml", b"pom"),
        factory("sources_jar", "demo-sources.jar", b"sources"),
    ]


def test_maven_upload_uses_settings_file_and_expected_files(
    mocker, monkeypatch, built_artifact, java_config, settings
):
    monkeypatch.setenv("BKREPO_PASSWORD", "inherited-secret")
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
    assert "BKREPO_PASSWORD" not in run.call_args.kwargs["env"]
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


def test_maven_partial_coordinate_uploads_only_missing_artifact(mocker, built_artifact, java_config, settings):
    settings.MAVEN_MIRRORS_CONFIG = {"default": {"repository_url": "https://repo/maven", "repository_id": "internal"}}
    artifacts = maven_artifacts(built_artifact)
    remote = mocker.patch(
        "apigateway.biz.sdk.publishers.maven.remote_sha256",
        side_effect=[
            (artifacts[0].sha256, artifacts[0].size),
            None,
            (artifacts[2].sha256, artifacts[2].size),
            (artifacts[1].sha256, artifacts[1].size),
        ],
    )
    upload = mocker.patch("apigateway.biz.sdk.publishers.maven.upload_file", create=True)

    results = publish_native("java", artifacts, java_config)

    upload.assert_called_once_with(
        artifacts[1].path,
        "https://repo/maven/com/tencent/bkapi/bkapi-demo/1.2.3/bkapi-demo-1.2.3.pom",
        username="",
        password="",
        verify=True,
    )
    assert remote.call_count == 4
    assert len(results) == 3


def test_maven_failure_redacts_repository_credentials(mocker, built_artifact, java_config, settings):
    settings.MAVEN_MIRRORS_CONFIG = {
        "default": {
            "repository_url": "https://repo/maven",
            "repository_id": "internal",
            "username": "sdk-user",
            "password": "sdk-password",
        }
    }
    mocker.patch("apigateway.biz.sdk.publishers.maven.remote_sha256", return_value=None)
    mocker.patch(
        "apigateway.biz.sdk.publishers.common.subprocess.run",
        return_value=subprocess.CompletedProcess([], 2, "", "token=maven-token password=sdk-password"),
    )

    with pytest.raises(SDKGenerateError) as exc_info:
        publish_native("java", maven_artifacts(built_artifact), java_config)

    message = str(exc_info.value)
    assert "sdk-password" not in message
    assert "maven-token" not in message
