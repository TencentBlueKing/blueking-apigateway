import subprocess

import pytest

from apigateway.biz.sdk.config import SDKLanguageConfig
from apigateway.biz.sdk.exceptions import SDKGenerateError
from apigateway.biz.sdk.generator import generate_client, get_openapi_generator_version


@pytest.fixture
def python_language_config():
    return SDKLanguageConfig(
        language="python",
        generator_name="python",
        project_name="bkapi-demo",
        package_name="bkapi_demo",
        package_version="1.2.3",
        additional_properties={
            "packageName": "bkapi_demo",
            "packageVersion": "1.2.3",
            "projectName": "bkapi-demo",
            "buildSystem": "poetry",
        },
        native_distributor=None,
    )


@pytest.mark.parametrize(
    ("language", "generator_name", "additional_properties"),
    [
        (
            "python",
            "python",
            {
                "packageName": "bkapi_openapi_demo",
                "packageVersion": "1.2.3",
                "projectName": "bkapi-openapi-demo",
                "buildSystem": "poetry",
            },
        ),
        (
            "java",
            "java",
            {
                "groupId": "com.tencent.bkapi",
                "artifactId": "bkapi-openapi-demo",
                "artifactVersion": "1.2.3",
                "invokerPackage": "com.tencent.bkapi.openapi.demo",
                "apiPackage": "com.tencent.bkapi.openapi.demo.api",
                "modelPackage": "com.tencent.bkapi.openapi.demo.model",
                "library": "native",
            },
        ),
        (
            "go",
            "go",
            {"packageName": "bkapi_demo", "packageVersion": "v1.2.3", "withGoMod": "true"},
        ),
        (
            "javascript",
            "typescript-fetch",
            {"npmName": "@bkapi/openapi-demo", "npmVersion": "1.2.3", "supportsES6": "true"},
        ),
    ],
)
def test_generate_client_uses_native_generator_and_fixed_coordinates(
    mocker, tmp_path, settings, language, generator_name, additional_properties
):
    config = SDKLanguageConfig(
        language=language,
        generator_name=generator_name,
        project_name=("git.example.com/bkapi/openapi/demo" if language == "go" else "bkapi-openapi-demo"),
        package_name=("@bkapi/openapi-demo" if language == "javascript" else "bkapi_openapi_demo"),
        package_version="v1.2.3" if language == "go" else "1.2.3",
        additional_properties=additional_properties,
        native_distributor=None,
    )
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    (tmp_path / "out").mkdir()
    run = mocker.patch("apigateway.biz.sdk.generator.subprocess.run")
    run.return_value = subprocess.CompletedProcess([], 0, "generated", "")

    generate_client(spec_path, tmp_path / "out", config)

    command = run.call_args.args[0]
    assert command[:5] == [
        "java",
        "-jar",
        settings.SDK_GENERATION["generator_jar"],
        "generate",
        "-i",
    ]
    assert command[command.index("-g") + 1] == generator_name
    encoded_properties = command[command.index("--additional-properties") + 1]
    assert set(encoded_properties.split(",")) == {
        *(f"{name}={value}" for name, value in additional_properties.items()),
        "hideGenerationTimestamp=true",
    }
    assert "bkapi-client-core" not in " ".join(command)
    assert "-t" not in command
    assert run.call_args.kwargs["shell"] is False
    assert run.call_args.kwargs["timeout"] == settings.SDK_GENERATION["subprocess_timeout_seconds"]
    assert run.call_args.kwargs["stdout"] is subprocess.DEVNULL
    assert run.call_args.kwargs["stderr"] is subprocess.PIPE


def test_generate_client_rejects_oversized_output(mocker, python_language_config, tmp_path, settings):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "client.py").write_bytes(b"oversized")
    settings.SDK_GENERATION = {**settings.SDK_GENERATION, "max_output_bytes": 4}
    mocker.patch(
        "apigateway.biz.sdk.generator.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    )

    with pytest.raises(SDKGenerateError, match="output exceeds"):
        generate_client(spec_path, output_dir, python_language_config)


@pytest.mark.parametrize(
    "result, expected_fragment",
    [
        (subprocess.CompletedProcess([], 2, "", "sensitive" * 1000), "exited with status 2"),
    ],
)
def test_generate_client_sanitizes_failures(mocker, python_language_config, tmp_path, result, expected_fragment):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    mocker.patch("apigateway.biz.sdk.generator.subprocess.run", return_value=result)

    with pytest.raises(SDKGenerateError) as exc_info:
        generate_client(spec_path, tmp_path / "out", python_language_config)

    assert exc_info.value.code == "generator_failed"
    assert exc_info.value.retryable is False
    assert expected_fragment in str(exc_info.value)
    assert "sensitive" in str(exc_info.value)
    assert len(str(exc_info.value)) < 1200


def test_generate_client_maps_timeout(mocker, python_language_config, tmp_path):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    mocker.patch(
        "apigateway.biz.sdk.generator.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["java"], 1),
    )

    with pytest.raises(SDKGenerateError) as exc_info:
        generate_client(spec_path, tmp_path / "out", python_language_config)

    assert exc_info.value.code == "generator_failed"
    assert exc_info.value.retryable is True
    assert "timed out" in str(exc_info.value)


def test_get_openapi_generator_version_requires_exact_pin(mocker, settings):
    run = mocker.patch("apigateway.biz.sdk.generator.subprocess.run")
    run.return_value = subprocess.CompletedProcess([], 0, "7.22.0\n", "")

    with pytest.raises(SDKGenerateError, match="expected 7.23.0"):
        get_openapi_generator_version()

    command = run.call_args.args[0]
    assert command == ["java", "-jar", settings.SDK_GENERATION["generator_jar"], "version"]
