import json
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from apigateway.biz.sdk.builders import build_artifacts
from apigateway.biz.sdk.config import SDKLanguageConfig
from apigateway.biz.sdk.exceptions import SDKGenerateError
from apigateway.biz.sdk.maven_settings import write_maven_settings
from apigateway.utils.maven import RepositoryConfig


def language_config(language):
    properties = {
        "python": {
            "packageName": "bkapi_demo",
            "packageVersion": "1.2.3",
            "projectName": "bkapi-demo",
            "buildSystem": "poetry",
        },
        "java": {
            "groupId": "com.tencent.bkapi",
            "artifactId": "bkapi-demo",
            "artifactVersion": "1.2.3",
            "invokerPackage": "com.tencent.bkapi.demo",
            "apiPackage": "com.tencent.bkapi.demo.api",
            "modelPackage": "com.tencent.bkapi.demo.model",
            "library": "native",
        },
        "go": {"packageName": "bkapi_demo", "packageVersion": "v1.2.3", "withGoMod": "true"},
        "javascript": {
            "npmName": "@bkapi/openapi-demo",
            "npmVersion": "1.2.3",
            "supportsES6": "true",
        },
    }[language]
    return SDKLanguageConfig(
        language=language,
        generator_name="typescript-fetch" if language == "javascript" else language,
        project_name="git.example.com/bkapi/openapi/demo" if language == "go" else "bkapi-openapi-demo",
        package_name="@bkapi/openapi-demo" if language == "javascript" else "bkapi_openapi_demo",
        package_version="v1.2.3" if language == "go" else "1.2.3",
        additional_properties=properties,
        native_distributor=None,
    )


def mock_build_commands(mocker, stdout, captured_settings):
    def run_command(command, **_kwargs):
        if command[0] == "mvn" and "-s" in command:
            settings_path = command[command.index("-s") + 1]
            captured_settings["content"] = Path(settings_path).read_text()
        return subprocess.CompletedProcess([], 0, stdout, "")

    return mocker.patch("apigateway.biz.sdk.builders.common.subprocess.run", side_effect=run_command)


def assert_cross_origin_maven_mirror_has_no_credentials(content):
    assert "https://maven.example.com/repository/public" in content
    assert "<mirror><id>sdk-mirror</id>" in content
    assert "<server><id>internal</id><username>user</username><password>secret</password>" in content
    assert "<server><id>sdk-mirror</id>" not in content


@pytest.mark.parametrize(
    ("language", "expected_types"),
    [
        ("python", {"wheel", "sdist"}),
        ("java", {"jar", "pom", "sources_jar", "distribution_zip"}),
        ("go", {"go_info", "go_mod", "go_zip"}),
        ("javascript", {"npm_tgz"}),
    ],
)
def test_builder_returns_ecosystem_artifacts(mocker, tmp_path, settings, language, expected_types):
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "dist"
    source_dir.mkdir()
    output_dir.mkdir()

    if language == "python":
        (output_dir / "demo-1.2.3-py3-none-any.whl").write_bytes(b"wheel")
        (output_dir / "demo-1.2.3.tar.gz").write_bytes(b"sdist")
    elif language == "java":
        settings.MAVEN_MIRRORS_CONFIG = {
            "default": {
                "repository_id": "internal",
                "username": "user",
                "password": "secret",
                "mirror_url": "https://maven.example.com/repository/public",
            }
        }
        target = source_dir / "target"
        target.mkdir()
        (target / "demo-1.2.3.jar").write_bytes(b"jar")
        (target / "demo-1.2.3-sources.jar").write_bytes(b"sources")
        (target / "demo-1.2.3-tests.jar").write_bytes(b"tests")
        (target / "demo-1.2.3-javadoc.jar").write_bytes(b"javadoc")
        (source_dir / "pom.xml").write_text("<project />")
    elif language == "go":
        (source_dir / "go.mod").write_text("module git.example.com/bkapi/openapi/demo\n")
        (source_dir / "client.go").write_text("package demo\n")
    elif language == "javascript":
        (output_dir / "bkapi-openapi-demo-1.2.3.tgz").write_bytes(b"npm")
    stdout = (
        "Successfully compiled 3 files with TypeScript\n" + json.dumps([{"filename": "bkapi-openapi-demo-1.2.3.tgz"}])
        if language == "javascript"
        else ""
    )
    captured_settings = {}
    run = mock_build_commands(mocker, stdout, captured_settings)
    validate_dependencies = mocker.patch(
        f"apigateway.biz.sdk.builders.{language}.validate_generated_dependency_inputs",
        create=True,
    )

    artifacts = build_artifacts(language, source_dir, output_dir, language_config(language))

    validate_dependencies.assert_called_once_with(language, source_dir)
    assert {artifact.artifact_type for artifact in artifacts} == expected_types
    assert all(artifact.sha256 and artifact.size > 0 for artifact in artifacts)
    command = run.call_args.args[0]
    assert command[0] == {"python": "python", "java": "mvn", "go": "go", "javascript": "npm"}[language]
    assert run.call_args.kwargs["shell"] is False
    assert all(call.kwargs["stderr"] is subprocess.PIPE for call in run.call_args_list)
    assert all("BKREPO_PASSWORD" not in call.kwargs["env"] for call in run.call_args_list)
    if language == "java":
        assert "-DincludeScope=runtime" in command
        assert "-s" in command
        assert_cross_origin_maven_mirror_has_no_credentials(captured_settings["content"])
        distribution = next(artifact.path for artifact in artifacts if artifact.artifact_type == "distribution_zip")
        with zipfile.ZipFile(distribution) as archive:
            assert "demo-1.2.3-tests.jar" not in archive.namelist()
    if language == "go":
        assert run.call_args_list[0].args[0] == [
            "go",
            "mod",
            "edit",
            "-module",
            "git.example.com/bkapi/openapi/demo",
        ]
    if language == "javascript":
        assert run.call_args_list[0].args[0] == [
            "npm",
            "install",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ]
        assert run.call_args_list[1].args[0] == ["npm", "run", "build", "--if-present"]
        assert run.call_args_list[2].args[0] == [
            "npm",
            "pack",
            "--ignore-scripts",
            "--json",
            "--pack-destination",
            str(output_dir),
        ]
        assert run.call_args_list[2].kwargs["stdout"] == subprocess.PIPE


def test_go_module_zip_has_required_prefix(mocker, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "go.mod").write_text("module git.example.com/bkapi/openapi/demo\n")
    (source_dir / "client.go").write_text("package demo\n")
    mocker.patch(
        "apigateway.biz.sdk.builders.common.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    )
    mocker.patch("apigateway.biz.sdk.builders.go.validate_generated_dependency_inputs", create=True)

    artifacts = build_artifacts("go", source_dir, tmp_path / "dist", language_config("go"))
    module_zip = next(item.path for item in artifacts if item.artifact_type == "go_zip")

    with zipfile.ZipFile(module_zip) as archive:
        assert all(name.startswith("git.example.com/bkapi/openapi/demo@v1.2.3/") for name in archive.namelist())


def test_builder_rejects_rust(tmp_path):
    with pytest.raises(ValueError, match="unsupported SDK builder language: rust"):
        build_artifacts("rust", tmp_path, tmp_path / "dist", SimpleNamespace(language="rust"))


def test_builder_redacts_failure_details(mocker, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    mocker.patch(
        "apigateway.biz.sdk.builders.common.subprocess.run",
        return_value=subprocess.CompletedProcess([], 2, "", "token=build-token password=build-password"),
    )
    mocker.patch("apigateway.biz.sdk.builders.python.validate_generated_dependency_inputs", create=True)

    with pytest.raises(SDKGenerateError) as exc_info:
        build_artifacts("python", source_dir, tmp_path / "dist", language_config("python"))

    assert "build-token" not in str(exc_info.value)
    assert "build-password" not in str(exc_info.value)


def test_maven_settings_reuses_deploy_credentials_for_same_origin_mirror(tmp_path):
    settings_path = tmp_path / "settings.xml"
    repository = RepositoryConfig(
        repository_url="https://maven.example.com/repository/releases",
        repository_id="internal",
        username="user",
        password="secret",
        mirror_url="https://maven.example.com/repository/public",
    )

    write_maven_settings(settings_path, repository)

    content = settings_path.read_text()
    assert "<mirror><id>internal</id>" in content
    assert content.count("<server><id>internal</id>") == 1
    assert "<server><id>sdk-mirror</id>" not in content
