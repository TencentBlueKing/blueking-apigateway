from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    USE_I18N=False,
    MAX_BACKEND_TIMEOUT_IN_SECOND=600,
    SDK_GENERATION={
        "subprocess_timeout_seconds": 1200,
        "max_artifact_bytes": 500 * 1024 * 1024,
    },
)
django.setup()

from apigateway.biz.sdk.artifacts import build_manifest  # noqa: E402
from apigateway.biz.sdk.builders import build_artifacts  # noqa: E402
from apigateway.biz.sdk.config import SDKLanguageConfig  # noqa: E402

ROOT = Path(__file__).parent
SPEC = ROOT / "minimal-openapi.yaml"
JAR = Path(os.environ["SDK_OPENAPI_GENERATOR_JAR"])

PROPERTIES = {
    "python": {
        "packageName": "bkapi_demo",
        "packageVersion": "1.2.3",
        "projectName": "bkapi-demo",
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
        "projectName": "bkapi-demo",
        "projectVersion": "1.2.3",
        "moduleName": "bkapi_demo",
        "usePromises": "true",
        "hideGenerationTimestamp": "true",
    },
    "rust": {
        "packageName": "bkapi_demo",
        "packageVersion": "1.2.3",
        "library": "reqwest",
        "supportAsync": "true",
        "hideGenerationTimestamp": "true",
    },
}


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def generate(language: str, destination: Path) -> SDKLanguageConfig:
    package_versions = {"go": "v1.2.3"}
    project_names = {"go": "example.com/blueking/bkapi-demo"}
    package_names = {"java": "com.example.bkapi.demo", "javascript": "bkapi-demo"}
    config = SDKLanguageConfig(
        language=language,
        generator_name=language,
        project_name=project_names.get(language, "bkapi-demo"),
        package_name=package_names.get(language, "bkapi_demo"),
        package_version=package_versions.get(language, "1.2.3"),
        additional_properties=PROPERTIES[language],
        native_distributor=None,
    )
    run(
        [
            "java",
            "-jar",
            str(JAR),
            "generate",
            "-i",
            str(SPEC),
            "-g",
            language,
            "-o",
            str(destination),
            "--additional-properties",
            ",".join(f"{key}={value}" for key, value in PROPERTIES[language].items()),
            "--global-property",
            "apiTests=false,modelTests=false,apiDocs=false,modelDocs=false",
        ],
        ROOT,
    )
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
    run([str(venv / "bin/python"), "-c", "import bkapi_demo"], root)


def verify_java(artifacts, root: Path) -> None:
    distribution = next(artifact.path for artifact in artifacts if artifact.artifact_type == "distribution_zip")
    unpacked = root / "java-distribution"
    with zipfile.ZipFile(distribution) as archive:
        archive.extractall(unpacked)
    classpath = ":".join(str(path) for path in unpacked.rglob("*.jar") if not path.name.endswith("-sources.jar"))
    source = root / "Consumer.java"
    source.write_text(
        "import com.example.bkapi.demo.ApiClient; "
        "public class Consumer { public static void main(String[] args) { new ApiClient(); } }"
    )
    run(["javac", "-cp", classpath, str(source)], root)


def verify_go(artifacts, root: Path) -> None:
    module_zip = next(artifact.path for artifact in artifacts if artifact.artifact_type == "go_zip")
    unpacked = root / "go-module"
    with zipfile.ZipFile(module_zip) as archive:
        archive.extractall(unpacked)
    module = next(path.parent for path in unpacked.rglob("go.mod"))
    run(["go", "test", "./..."], module)


def verify_javascript(artifacts, root: Path) -> None:
    package = next(artifact.path for artifact in artifacts if artifact.artifact_type == "npm_tgz")
    project = root / "javascript-consumer"
    project.mkdir()
    run(["npm", "init", "-y"], project)
    run(["npm", "install", "--ignore-scripts", str(package)], project)
    run(["node", "-e", "require('bkapi-demo')"], project)


def verify_rust(artifacts, root: Path) -> None:
    crate = next(artifact.path for artifact in artifacts if artifact.artifact_type == "crate")
    unpacked = root / "rust-crate"
    unpacked.mkdir()
    with tarfile.open(crate) as archive:
        archive.extractall(unpacked, filter="data")
    crate_root = next(path.parent for path in unpacked.rglob("Cargo.toml"))
    project = root / "rust-consumer"
    (project / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text(
        '[package]\nname = "consumer"\nversion = "0.1.0"\nedition = "2021"\n'
        f"[dependencies]\nbkapi_demo = {{ path = {json.dumps(str(crate_root))} }}\n"
    )
    (project / "src/main.rs").write_text(
        "fn main() { let _ = bkapi_demo::apis::configuration::Configuration::new(); }\n"
    )
    run(["cargo", "check"], project)


VERIFIERS = {
    "python": verify_python,
    "java": verify_java,
    "go": verify_go,
    "javascript": verify_javascript,
    "rust": verify_rust,
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
