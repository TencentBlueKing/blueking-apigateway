import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from apigateway.biz.sdk.exceptions import SDKConfigurationError
from apigateway.biz.sdk.toolchain import (
    SDKToolchainIdentity,
    probe_toolchain_identity,
    validate_generated_dependency_inputs,
)


@pytest.fixture(autouse=True)
def configure_bkrepo_generic(settings):
    settings.BKREPO_ENDPOINT_URL = "https://bkrepo.example.com"
    settings.BKREPO_USERNAME = "sdk-user"
    settings.BKREPO_PASSWORD = "sdk-password"
    settings.BKREPO_PROJECT = "sdk-project"
    settings.BKREPO_GENERIC_BUCKET = "sdk-generic"


def test_probe_toolchain_identity_reads_every_tool_once(mocker, tmp_path):
    lock_file = tmp_path / "sdk-worker-lock.json"
    lock_file.write_text('{"format_version":1}')
    mocker.patch("apigateway.biz.sdk.toolchain.SDK_WORKER_LOCK_FILE", str(lock_file))
    outputs = iter(
        ["7.23.0", "Python 3.14.1", "openjdk 17.0.15", "Apache Maven 3.9.9", "go1.24.4", "v22.17.0", "11.4.2"]
    )
    run_version = mocker.patch("apigateway.biz.sdk.toolchain._run_version_command", side_effect=outputs)
    probe_toolchain_identity.cache_clear()

    identity = probe_toolchain_identity()
    assert identity == SDKToolchainIdentity(
        openapi_generator="7.23.0",
        python="3.14.1",
        java="17.0.15",
        maven="3.9.9",
        go="1.24.4",
        node="22.17.0",
        npm="11.4.2",
        dependency_lock_sha256="d88bf399e67c0574c03d47dd19ec99ebe1641083faa6688893cd902eb6051a3f",
    )
    assert run_version.call_count == 7

    assert probe_toolchain_identity() is identity
    assert run_version.call_count == 7


def test_probe_toolchain_identity_rejects_missing_lock(mocker, tmp_path):
    mocker.patch("apigateway.biz.sdk.toolchain.SDK_WORKER_LOCK_FILE", str(tmp_path / "missing.json"))
    probe_toolchain_identity.cache_clear()

    with pytest.raises(SDKConfigurationError, match="lock file"):
        probe_toolchain_identity()


def test_toolchain_identity_is_immutable():
    identity = SDKToolchainIdentity("7.23.0", "3.14.1", "17.0.15", "3.9.9", "1.24.4", "22.17.0", "11.4.2", "a" * 64)

    with pytest.raises(FrozenInstanceError):
        identity.go = "changed"
    assert replace(identity, go="1.24.5").go == "1.24.5"


def test_checked_in_worker_lock_covers_four_language_dependencies(settings):
    lock_path = Path(settings.BASE_DIR).parents[1] / "sdk-worker-lock.json"

    lock = json.loads(lock_path.read_text())

    assert lock["openapi_generator"] == {
        "version": "7.23.0",
        "jar_sha256": "cb087e40001e31eb08ef6140dd5de10938dbeb89016a1fe0481eaa25cd569026",
    }
    assert set(lock["generated_dependencies"]) == {"python", "java", "go", "javascript"}
    assert lock["generated_dependencies"]["javascript"]["package_lock_integrities_sha256"]


def test_validate_generated_javascript_dependencies_uses_package_lock_integrities(mocker, tmp_path):
    package = {"dependencies": {"superagent": "^5.3.0"}}
    package_lock = {
        "packages": {
            "": {"name": "@bkapi/openapi-demo"},
            "node_modules/superagent": {
                "version": "5.3.1",
                "integrity": "sha512-example",
            },
        }
    }
    integrity_records = [
        {
            "package": "node_modules/superagent",
            "version": "5.3.1",
            "integrity": "sha512-example",
        }
    ]
    integrity_hash = hashlib.sha256(
        json.dumps(integrity_records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    lock = {
        "format_version": 1,
        "generated_dependencies": {
            "python": {},
            "java": {},
            "go": {},
            "javascript": {
                "runtime_ranges": package["dependencies"],
                "development_ranges": {},
                "package_lock_integrities_sha256": integrity_hash,
            },
        },
    }
    (tmp_path / "package.json").write_text(json.dumps(package))
    (tmp_path / "package-lock.json").write_text(json.dumps(package_lock))
    lock_path = tmp_path / "sdk-worker-lock.json"
    lock_path.write_text(json.dumps(lock))
    mocker.patch("apigateway.biz.sdk.toolchain.SDK_WORKER_LOCK_FILE", str(lock_path))

    validate_generated_dependency_inputs("javascript", tmp_path)

    package_lock["packages"]["node_modules/superagent"]["integrity"] = "sha512-changed"
    (tmp_path / "package-lock.json").write_text(json.dumps(package_lock))
    with pytest.raises(SDKConfigurationError, match="JavaScript dependencies"):
        validate_generated_dependency_inputs("javascript", tmp_path)
