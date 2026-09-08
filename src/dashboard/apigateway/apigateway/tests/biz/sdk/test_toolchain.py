import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from apigateway.biz.sdk.exceptions import SDKConfigurationError
from apigateway.biz.sdk.toolchain import (
    SDKToolchainIdentity,
    prepare_generated_dependency_inputs,
    probe_toolchain_identity,
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
    assert lock["generated_dependencies"]["javascript"]["package_lock"]["packages"]["node_modules/typescript"][
        "integrity"
    ]


def test_javascript_dependencies_are_locked_before_install(mocker, tmp_path, settings):
    lock_path = Path(settings.BASE_DIR).parents[1] / "sdk-worker-lock.json"
    package = {
        "name": "@custom/openapi-gateway",
        "version": "2.3.4",
        "devDependencies": {"typescript": "^4.0 || ^5.0"},
    }
    (tmp_path / "package.json").write_text(json.dumps(package))
    mocker.patch("apigateway.biz.sdk.toolchain.SDK_WORKER_LOCK_FILE", str(lock_path))

    prepare_generated_dependency_inputs("javascript", tmp_path)

    installed_lock = json.loads((tmp_path / "package-lock.json").read_text())
    assert installed_lock["name"] == package["name"]
    assert installed_lock["version"] == package["version"]
    assert installed_lock["packages"][""]["name"] == package["name"]
    assert installed_lock["packages"]["node_modules/typescript"]["version"] == "5.9.3"
    assert installed_lock["packages"]["node_modules/typescript"]["integrity"]

    package["devDependencies"]["typescript"] = "^6.0"
    (tmp_path / "package.json").write_text(json.dumps(package))
    with pytest.raises(SDKConfigurationError, match="JavaScript dependencies"):
        prepare_generated_dependency_inputs("javascript", tmp_path)
