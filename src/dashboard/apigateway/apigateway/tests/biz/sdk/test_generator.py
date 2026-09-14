#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import ast
import json
import subprocess
import tomllib

import pytest

from apigateway.biz.sdk.config import SDK_OPENAPI_GENERATOR_JAR, SDKLanguageConfig
from apigateway.biz.sdk.exceptions import SDKGenerationError
from apigateway.biz.sdk.generator import generate_client


def write_runtime_descriptors(output_dir, language):
    if language == "python":
        (output_dir / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.9"\n')
        (output_dir / "setup.py").write_text('PYTHON_REQUIRES = ">= 3.10"\nsetup(\n    name="demo",\n)\n')
        (output_dir / "README.md").write_text("# demo\n\n## Requirements.\n\nPython 3.10+\n")
    elif language == "javascript":
        (output_dir / "package.json").write_text('{"name":"demo","engines":{"npm":">=10"}}')
        (output_dir / "README.md").write_text("# demo\n")


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
                "groupId": "com.tencent.bk.bkapi",
                "artifactId": "bkapi-openapi-demo",
                "artifactVersion": "1.2.3",
                "invokerPackage": "com.tencent.bk.bkapi.openapi.demo",
                "apiPackage": "com.tencent.bk.bkapi.openapi.demo.api",
                "modelPackage": "com.tencent.bk.bkapi.openapi.demo.model",
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
        project_name=("bk.tencent.com/bkapi/openapi/demo" if language == "go" else "bkapi-openapi-demo"),
        package_name=("@bkapi/openapi-demo" if language == "javascript" else "bkapi_openapi_demo"),
        package_version="v1.2.3" if language == "go" else "1.2.3",
        additional_properties=additional_properties,
        native_distributor=None,
    )
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    (tmp_path / "out").mkdir()
    write_runtime_descriptors(tmp_path / "out", language)
    run = mocker.patch("apigateway.biz.sdk.generator.subprocess.run")
    run.return_value = subprocess.CompletedProcess([], 0, "generated", "")

    generate_client(spec_path, tmp_path / "out", config)

    command = run.call_args.args[0]
    assert command[:5] == [
        "java",
        "-jar",
        SDK_OPENAPI_GENERATOR_JAR,
        "generate",
        "-i",
    ]
    assert command[command.index("-g") + 1] == generator_name
    encoded_properties = command[command.index("--additional-properties") + 1]
    assert set(encoded_properties.split(",")) == {
        *(f"{name}={value}" for name, value in additional_properties.items()),
        "hideGenerationTimestamp=true",
    }
    global_properties = command[command.index("--global-property") + 1]
    assert {"apiTests=false", "modelTests=false"}.issubset(global_properties.split(","))
    assert "bkapi-client-core" not in " ".join(command)
    assert "-t" not in command
    assert run.call_args.kwargs["shell"] is False
    assert run.call_args.kwargs["timeout"] == settings.SDK_SUBPROCESS_TIMEOUT_SECONDS
    assert run.call_args.kwargs["stdout"] is subprocess.DEVNULL
    assert run.call_args.kwargs["stderr"] is subprocess.PIPE
    assert "BKREPO_PASSWORD" not in run.call_args.kwargs["env"]

    if language == "python":
        output_dir = tmp_path / "out"
        metadata = tomllib.loads((output_dir / "pyproject.toml").read_text())
        assert metadata["project"]["requires-python"] == ">=3.10"
        setup = ast.parse((output_dir / "setup.py").read_text())
        assert setup.body[0].value.value == ">=3.10"
        assert any(keyword.arg == "python_requires" for keyword in setup.body[1].value.keywords)
        assert "Python >=3.10" in (output_dir / "README.md").read_text()
        assert config.build_fingerprint_payload()["runtime_requirement"] == ">=3.10"
    elif language == "javascript":
        package = json.loads((tmp_path / "out" / "package.json").read_text())
        assert package["engines"] == {"node": ">=22", "npm": ">=10"}
        readme = (tmp_path / "out" / "README.md").read_text()
        assert "Node.js >=22" in readme
        assert "Fetch" in readme
        assert "No polyfills are bundled" in readme
        assert config.build_fingerprint_payload()["runtime_requirement"] == ">=22"


def test_generate_client_rejects_missing_runtime_metadata(mocker, tmp_path, python_language_config):
    spec = tmp_path / "openapi.json"
    spec.write_text("{}")
    output = tmp_path / "out"
    output.mkdir()
    mocker.patch("apigateway.biz.sdk.generator.subprocess.run", return_value=subprocess.CompletedProcess([], 0))
    with pytest.raises(SDKGenerationError, match="cannot apply SDK runtime requirements"):
        generate_client(spec, output, python_language_config)


def test_generate_client_rejects_changed_runtime_declaration(mocker, tmp_path, python_language_config):
    spec = tmp_path / "openapi.json"
    spec.write_text("{}")
    output = tmp_path / "out"
    output.mkdir()
    write_runtime_descriptors(output, "python")
    (output / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    mocker.patch("apigateway.biz.sdk.generator.subprocess.run", return_value=subprocess.CompletedProcess([], 0))
    with pytest.raises(SDKGenerationError, match="unexpected runtime declaration"):
        generate_client(spec, output, python_language_config)


def test_generate_client_rejects_oversized_output(mocker, python_language_config, tmp_path, settings):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "client.py").write_bytes(b"oversized")
    settings.SDK_MAX_OUTPUT_BYTES = 4
    mocker.patch(
        "apigateway.biz.sdk.generator.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    )

    with pytest.raises(SDKGenerationError, match="output exceeds"):
        generate_client(spec_path, output_dir, python_language_config)


@pytest.mark.parametrize(
    "result, expected_fragment",
    [
        (subprocess.CompletedProcess([], 2, "", "password=sdk-password"), "exited with status 2"),
    ],
)
def test_generate_client_sanitizes_failures(mocker, python_language_config, tmp_path, result, expected_fragment):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    mocker.patch("apigateway.biz.sdk.generator.subprocess.run", return_value=result)

    with pytest.raises(SDKGenerationError) as exc_info:
        generate_client(spec_path, tmp_path / "out", python_language_config)

    assert exc_info.value.code == "generator_failed"
    assert exc_info.value.retryable is False
    assert expected_fragment in str(exc_info.value)
    assert "sdk-password" not in str(exc_info.value)
    assert "password=***" in str(exc_info.value)
    assert len(str(exc_info.value)) < 1200


def test_generate_client_maps_timeout(mocker, python_language_config, tmp_path):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{}")
    mocker.patch(
        "apigateway.biz.sdk.generator.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["java"], 1),
    )

    with pytest.raises(SDKGenerationError) as exc_info:
        generate_client(spec_path, tmp_path / "out", python_language_config)

    assert exc_info.value.code == "generator_failed"
    assert exc_info.value.retryable is True
    assert "timed out" in str(exc_info.value)
