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
from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    USE_I18N=False,
    MAX_BACKEND_TIMEOUT_IN_SECOND=600,
    SDK_GENERATION_ENABLED=True,
    SDK_ENABLED_LANGUAGES=["python", "java", "go", "javascript"],
    SDK_GENERATION_RETRY_DELAYS=(30, 120),
    SDK_PYTHON_DISTRIBUTION_PREFIX="bkapi-openapi",
    SDK_JAVA_GROUP_ID="com.example.bkapi",
    SDK_JAVA_PACKAGE_PREFIX="com.example.bkapi",
    SDK_GO_MODULE_PREFIX="example.com/blueking",
    SDK_JAVASCRIPT_PACKAGE_SCOPE="@bkapi",
    BKREPO_ENDPOINT_URL="https://repo.example.com",
    BKREPO_USERNAME="smoke",
    BKREPO_PASSWORD="smoke",
    BKREPO_PROJECT="smoke",
    BKREPO_GENERIC_BUCKET="smoke",
    PYPI_MIRRORS_CONFIG={"default": {}},
    MAVEN_MIRRORS_CONFIG={
        "default": {
            "repository_url": "",
            "repository_id": "central",
            "username": "",
            "password": "",
            "ssl_insecure": False,
            "mirror_url": "https://repo.maven.apache.org/maven2",
        }
    },
    SDK_GENERATION_QUEUE="sdk.generate",
    SDK_SERVER_URL_TEMPLATE="https://{gateway_name}.example.com/{stage_name}",
    SDK_GENERIC_RETENTION_HOURS=24,
    SDK_SUBPROCESS_TIMEOUT_SECONDS=1200,
    SDK_MAX_OPENAPI_BYTES=10 * 1024 * 1024,
    SDK_MAX_OUTPUT_BYTES=1024 * 1024 * 1024,
    SDK_MAX_ARTIFACT_BYTES=500 * 1024 * 1024,
)
django.setup()

from apigateway.biz.sdk.artifacts import build_manifest  # noqa: E402
from apigateway.biz.sdk.builders import build_artifacts  # noqa: E402
from apigateway.biz.sdk.config import SDKLanguageConfig  # noqa: E402
from apigateway.biz.sdk.generator import generate_client  # noqa: E402

ROOT = Path(__file__).parent
SPEC = ROOT / "minimal-openapi.yaml"

PROPERTIES = {
    "python": {
        "packageName": "bkapi_openapi_demo",
        "packageVersion": "1.2.3",
        "projectName": "bkapi-openapi-demo",
        "buildSystem": "poetry",
        "hideGenerationTimestamp": "true",
    },
    "java": {
        "groupId": "com.example.bkapi",
        "artifactId": "bkapi-demo",
        "artifactVersion": "1.2.3",
        "invokerPackage": "com.example.bkapi.demo",
        "apiPackage": "com.example.bkapi.demo.api",
        "modelPackage": "com.example.bkapi.demo.model",
        "library": "native",
        "hideGenerationTimestamp": "true",
    },
    "go": {
        "packageName": "bkapi_demo",
        "packageVersion": "v1.2.3",
        "withGoMod": "true",
        "hideGenerationTimestamp": "true",
    },
    "javascript": {
        "npmName": "@bkapi/openapi-demo",
        "npmVersion": "1.2.3",
        "supportsES6": "true",
        "hideGenerationTimestamp": "true",
    },
}

GENERATORS = {
    "python": "python",
    "java": "java",
    "go": "go",
    "javascript": "typescript-fetch",
}


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def generate(language: str, destination: Path) -> SDKLanguageConfig:
    package_versions = {"go": "v1.2.3"}
    project_names = {
        "go": "example.com/blueking/openapi/demo",
        "javascript": "@bkapi/openapi-demo",
    }
    package_names = {
        "java": "com.example.bkapi.demo",
        "javascript": "@bkapi/openapi-demo",
        "python": "bkapi_openapi_demo",
    }
    config = SDKLanguageConfig(
        language=language,
        generator_name=GENERATORS[language],
        project_name=project_names.get(language, "bkapi-openapi-demo"),
        package_name=package_names.get(language, "bkapi_demo"),
        package_version=package_versions.get(language, "1.2.3"),
        additional_properties=PROPERTIES[language],
        native_distributor=None,
    )
    generate_client(SPEC, destination, config)
    return config


def verify_manifest(language: str, config: SDKLanguageConfig, artifacts) -> None:
    manifest = build_manifest(
        "demo", "1.2.3", language, config.package_version, "0" * 64, {"openapi-generator": "7.23.0"}, artifacts
    )
    by_name = {artifact.filename: artifact for artifact in artifacts}
    for file in manifest.files:
        assert hashlib.sha256(by_name[file.filename].path.read_bytes()).hexdigest() == file.sha256


def verify_python(artifacts, root: Path) -> None:
    wheel = next(artifact.path for artifact in artifacts if artifact.artifact_type == "wheel")
    venv = root / "venv"
    run(["python", "-m", "venv", str(venv)], root)
    run([str(venv / "bin/pip"), "install", str(wheel)], root)
    run(
        [
            str(venv / "bin/python"),
            "-c",
            (
                "import bkapi_openapi_demo\n"
                "configuration = bkapi_openapi_demo.Configuration(host='https://api.example.com/prod')\n"
                "with bkapi_openapi_demo.ApiClient(configuration) as api_client:\n"
                "    bkapi_openapi_demo.DefaultApi(api_client)\n"
            ),
        ],
        root,
    )


def verify_java(artifacts, root: Path) -> None:
    distribution = next(artifact.path for artifact in artifacts if artifact.artifact_type == "distribution_zip")
    unpacked = root / "java-distribution"
    with zipfile.ZipFile(distribution) as archive:
        archive.extractall(unpacked)
    classpath = os.pathsep.join(
        str(path) for path in unpacked.rglob("*.jar") if not path.name.endswith("-sources.jar")
    )
    source = root / "Consumer.java"
    source.write_text(
        "import com.example.bkapi.demo.ApiClient;\n"
        "import com.example.bkapi.demo.api.DefaultApi;\n"
        "public class Consumer { public static void main(String[] args) {\n"
        '  ApiClient client = new ApiClient(); client.updateBaseUri("https://api.example.com/prod");\n'
        "  new DefaultApi(client);\n"
        "} }\n"
    )
    run(["javac", "-cp", classpath, str(source)], root)
    run(["java", "-cp", f"{classpath}{os.pathsep}{root}", "Consumer"], root)


def verify_go(artifacts, root: Path) -> None:
    module_zip = next(artifact.path for artifact in artifacts if artifact.artifact_type == "go_zip")
    unpacked = root / "go-module"
    with zipfile.ZipFile(module_zip) as archive:
        archive.extractall(unpacked)
    module = next(path.parent for path in unpacked.rglob("go.mod"))
    consumer = root / "consumer"
    consumer.mkdir()
    (consumer / "go.mod").write_text(
        "module sdk-smoke-consumer\n\n"
        "go 1.23\n\n"
        "require example.com/blueking/openapi/demo v1.2.3\n\n"
        f"replace example.com/blueking/openapi/demo => {module}\n"
    )
    (consumer / "main.go").write_text(
        'package main\n\nimport sdk "example.com/blueking/openapi/demo"\n\n'
        "func main() { _ = sdk.NewAPIClient(sdk.NewConfiguration()) }\n"
    )
    run(["go", "test", "./..."], consumer)


def verify_javascript(artifacts, root: Path) -> None:
    package = next(artifact.path for artifact in artifacts if artifact.artifact_type == "npm_tgz")
    project = root / "javascript-consumer"
    project.mkdir()
    run(["npm", "init", "-y"], project)
    run(["npm", "install", "--ignore-scripts", str(package)], project)
    run(
        [
            "node",
            "-e",
            (
                "const sdk = require('@bkapi/openapi-demo'); "
                "const config = new sdk.Configuration({basePath: 'https://api.example.com/prod', apiKey: 'smoke'}); "
                "new sdk.DefaultApi(config);"
            ),
        ],
        project,
    )


VERIFIERS = {
    "python": verify_python,
    "java": verify_java,
    "go": verify_go,
    "javascript": verify_javascript,
}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sdk-worker-smoke-") as directory:
        root = Path(directory)
        for language, verifier in VERIFIERS.items():
            source = root / language / "source"
            output = root / language / "dist"
            config = generate(language, source)
            artifacts = build_artifacts(language, source, output, config)
            verify_manifest(language, config, artifacts)
            verifier(artifacts, root / language)
            print(f"{language}: smoke passed")


if __name__ == "__main__":
    main()
