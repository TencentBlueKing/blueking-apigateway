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


def test_generate_python_uses_official_generator(mocker, python_language_config, tmp_path, settings):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    run = mocker.patch("apigateway.biz.sdk.generator.subprocess.run")
    run.return_value = subprocess.CompletedProcess([], 0, "generated", "")

    generate_client(spec_path, tmp_path / "out", python_language_config)

    command = run.call_args.args[0]
    assert command[:5] == [
        "java",
        "-jar",
        settings.SDK_GENERATION["generator_jar"],
        "generate",
        "-i",
    ]
    assert command[command.index("-g") + 1] == "python"
    assert "buildSystem=poetry" in command[command.index("--additional-properties") + 1]
    assert run.call_args.kwargs["shell"] is False
    assert run.call_args.kwargs["timeout"] == settings.SDK_GENERATION["subprocess_timeout_seconds"]
    assert run.call_args.kwargs["stdout"] is subprocess.DEVNULL
    assert run.call_args.kwargs["stderr"] is subprocess.DEVNULL


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
    assert expected_fragment in str(exc_info.value)
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
    assert "timed out" in str(exc_info.value)


def test_get_openapi_generator_version_requires_exact_pin(mocker, settings):
    run = mocker.patch("apigateway.biz.sdk.generator.subprocess.run")
    run.return_value = subprocess.CompletedProcess([], 0, "7.22.0\n", "")

    with pytest.raises(SDKGenerateError, match="expected 7.23.0"):
        get_openapi_generator_version()

    command = run.call_args.args[0]
    assert command == ["java", "-jar", settings.SDK_GENERATION["generator_jar"], "version"]
