"""SDK worker toolchain probing and lock validation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from apigateway.biz.sdk.config import get_sdk_worker_config
from apigateway.biz.sdk.exceptions import SDKConfigurationError

VERSION_PATTERN = re.compile(r"(?:go|v)?(\d+\.\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class SDKToolchainIdentity:
    openapi_generator: str
    python: str
    java: str
    maven: str
    go: str
    node: str
    npm: str
    dependency_lock_sha256: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _run_version_command(command: list[str]) -> str:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SDKConfigurationError(f"SDK tool is unavailable: {command[0]}") from error
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout).split())[:256]
        raise SDKConfigurationError(f"SDK tool version probe failed: {command[0]}: {detail}")
    return (result.stdout or result.stderr).strip()


def _normalize_version(output: str, tool: str) -> str:
    if match := VERSION_PATTERN.search(output):
        return match.group(1)
    raise SDKConfigurationError(f"cannot determine {tool} version")


@lru_cache(maxsize=1)
def probe_toolchain_identity() -> SDKToolchainIdentity:
    config = get_sdk_worker_config()
    lock_path = Path(config.worker_lock_file)
    try:
        lock_bytes = lock_path.read_bytes()
    except OSError as error:
        raise SDKConfigurationError(f"SDK worker lock file is unavailable: {lock_path}") from error

    commands = {
        "openapi_generator": ["java", "-jar", config.generator_jar, "version"],
        "python": ["python", "--version"],
        "java": ["java", "-version"],
        "maven": ["mvn", "--version"],
        "go": ["go", "version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
    }
    versions = {name: _normalize_version(_run_version_command(command), name) for name, command in commands.items()}
    return SDKToolchainIdentity(
        **versions,
        dependency_lock_sha256=hashlib.sha256(lock_bytes).hexdigest(),
    )


def _load_worker_lock(path: str) -> dict[str, object]:
    try:
        content = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise SDKConfigurationError(f"SDK worker lock file is invalid: {path}") from error
    if content.get("format_version") != 1:
        raise SDKConfigurationError("SDK worker lock format is unsupported")
    dependencies = content.get("generated_dependencies")
    if not isinstance(dependencies, dict) or set(dependencies) != {"python", "java", "go", "javascript"}:
        raise SDKConfigurationError("SDK worker lock must describe all generated dependencies")
    return content


def validate_sdk_worker_environment() -> dict[str, str]:
    config = get_sdk_worker_config()
    lock = _load_worker_lock(config.worker_lock_file)
    identity = probe_toolchain_identity()
    expected_generator = lock.get("openapi_generator")
    expected_toolchains = lock.get("toolchains")
    if not isinstance(expected_generator, dict) or not isinstance(expected_toolchains, dict):
        raise SDKConfigurationError("SDK worker lock is missing toolchain identities")
    if identity.openapi_generator != config.generator_version or identity.openapi_generator != expected_generator.get(
        "version"
    ):
        raise SDKConfigurationError("OpenAPI Generator version does not match the worker lock")

    jar_path = Path(config.generator_jar)
    try:
        jar_sha256 = hashlib.sha256(jar_path.read_bytes()).hexdigest()
    except OSError as error:
        raise SDKConfigurationError(f"OpenAPI Generator JAR is unavailable: {jar_path}") from error
    if jar_sha256 != expected_generator.get("jar_sha256"):
        raise SDKConfigurationError("OpenAPI Generator JAR checksum does not match the worker lock")

    actual = identity.as_dict()
    for tool in ("python", "java", "maven", "go", "node", "npm"):
        expected = expected_toolchains.get(tool)
        if not isinstance(expected, str) or not actual[tool].startswith(expected):
            raise SDKConfigurationError(f"{tool} version does not match the worker lock")
    return actual


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as error:
        raise SDKConfigurationError(f"generated dependency descriptor is unavailable: {path.name}") from error


def validate_generated_dependency_inputs(language: str, output_dir: Path) -> None:
    config = get_sdk_worker_config()
    lock = _load_worker_lock(config.worker_lock_file)
    dependencies = lock["generated_dependencies"]
    if not isinstance(dependencies, dict) or not isinstance(expected := dependencies.get(language), dict):
        raise SDKConfigurationError(f"generated dependency lock is unavailable for {language}")

    if language == "python":
        requirements = [line for line in _read_text(output_dir / "requirements.txt").splitlines() if line]
        if requirements != expected.get("requirements"):
            raise SDKConfigurationError("generated Python dependencies do not match the worker lock")
        return

    if language == "java":
        root = ET.fromstring(_read_text(output_dir / "pom.xml"))
        namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
        properties = root.find("m:properties", namespace)
        actual_properties = {child.tag.rsplit("}", 1)[-1]: child.text for child in properties or []}
        if any(actual_properties.get(name) != value for name, value in expected.get("properties", {}).items()):
            raise SDKConfigurationError("generated Java dependencies do not match the worker lock")
        direct_versions = {
            f"{dependency.findtext('m:groupId', namespaces=namespace)}:{dependency.findtext('m:artifactId', namespaces=namespace)}": dependency.findtext(
                "m:version", namespaces=namespace
            )
            for dependency in root.findall("m:dependencies/m:dependency", namespace)
        }
        if any(direct_versions.get(name) != value for name, value in expected.get("direct_versions", {}).items()):
            raise SDKConfigurationError("generated Java dependencies do not match the worker lock")
        return

    if language == "go":
        go_mod = _read_text(output_dir / "go.mod")
        go_version = next((line.removeprefix("go ") for line in go_mod.splitlines() if line.startswith("go ")), "")
        module_sums = [line for line in _read_text(output_dir / "go.sum").splitlines() if line]
        if go_version != expected.get("go_version") or module_sums != expected.get("module_sums"):
            raise SDKConfigurationError("generated Go dependencies do not match the worker lock")
        return

    if language == "javascript":
        package = json.loads(_read_text(output_dir / "package.json"))
        package_lock = json.loads(_read_text(output_dir / "package-lock.json"))
        integrity_records = [
            {"package": name, "version": value.get("version"), "integrity": value["integrity"]}
            for name, value in package_lock.get("packages", {}).items()
            if "integrity" in value
        ]
        integrity_hash = hashlib.sha256(
            json.dumps(integrity_records, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if (
            package.get("dependencies", {}) != expected.get("runtime_ranges")
            or package.get("devDependencies", {}) != expected.get("development_ranges")
            or integrity_hash != expected.get("package_lock_integrities_sha256")
        ):
            raise SDKConfigurationError("generated JavaScript dependencies do not match the worker lock")
        return

    raise SDKConfigurationError(f"unsupported generated dependency language: {language}")
