import subprocess
from types import SimpleNamespace

import pytest

from apigateway.biz.sdk.exceptions import SDKArtifactConflict, SDKGenerateError
from apigateway.biz.sdk.publishers import publish_native


def test_disabled_native_repository_returns_no_artifacts(built_artifact, python_config, settings):
    settings.PYPI_MIRRORS_CONFIG = {"default": {}}

    assert (
        publish_native(
            "python",
            [built_artifact("wheel", "demo.whl"), built_artifact("sdist", "demo.tar.gz")],
            python_config,
        )
        == []
    )


def test_pypi_upload_uses_temporary_config_without_secret_in_command(
    mocker, monkeypatch, built_artifact, python_config, settings
):
    monkeypatch.setenv("BKREPO_PASSWORD", "inherited-secret")
    settings.PYPI_MIRRORS_CONFIG = {
        "default": {
            "index_url": "https://repo/simple",
            "repository_url": "https://repo/upload",
            "username": "user",
            "password": "secret",
        }
    }
    wheel = built_artifact("wheel", "demo.whl")
    sdist = built_artifact("sdist", "demo.tar.gz")
    search = mocker.patch(
        "apigateway.biz.sdk.publishers.pypi.SimplePypiRegistry.search",
        side_effect=[
            None,
            None,
            SimpleNamespace(url="https://repo/packages/demo.whl"),
            SimpleNamespace(url="https://repo/packages/demo.tar.gz"),
        ],
    )
    mocker.patch(
        "apigateway.biz.sdk.publishers.pypi.remote_sha256",
        side_effect=[(wheel.sha256, wheel.size), (sdist.sha256, sdist.size)],
    )
    run = mocker.patch(
        "apigateway.biz.sdk.publishers.common.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    )

    results = publish_native(
        "python",
        [wheel, sdist],
        python_config,
    )

    command = run.call_args.args[0]
    assert command[:2] == ["twine", "upload"]
    assert "secret" not in " ".join(command)
    assert {result.artifact_type for result in results} == {"wheel", "sdist"}
    assert {result.url for result in results} == {
        "https://repo/packages/demo.whl",
        "https://repo/packages/demo.tar.gz",
    }
    assert search.call_count == 4
    assert run.call_args.kwargs["stderr"] is subprocess.PIPE
    assert "BKREPO_PASSWORD" not in run.call_args.kwargs["env"]


def test_pypi_matching_remote_is_reused(mocker, built_artifact, python_config, settings):
    settings.PYPI_MIRRORS_CONFIG = {
        "default": {
            "index_url": "https://repo/simple",
            "repository_url": "https://repo/upload",
            "username": "",
            "password": "",
        }
    }
    wheel = built_artifact("wheel", "demo.whl")
    sdist = built_artifact("sdist", "demo.tar.gz")
    packages = [SimpleNamespace(url="https://repo/demo.whl"), SimpleNamespace(url="https://repo/demo.tar.gz")]
    mocker.patch("apigateway.biz.sdk.publishers.pypi.SimplePypiRegistry.search", side_effect=packages)
    mocker.patch(
        "apigateway.biz.sdk.publishers.pypi.remote_sha256",
        side_effect=[(wheel.sha256, wheel.size), (sdist.sha256, sdist.size)],
    )
    run = mocker.patch("apigateway.biz.sdk.publishers.common.subprocess.run")

    results = publish_native("python", [wheel, sdist], python_config)

    assert len(results) == 2
    run.assert_not_called()


def test_pypi_does_not_send_repository_credentials_to_cross_origin_package_urls(
    mocker, built_artifact, python_config, settings
):
    settings.PYPI_MIRRORS_CONFIG = {
        "default": {
            "index_url": "https://repo.example.com/simple",
            "repository_url": "https://repo.example.com/upload",
            "username": "user",
            "password": "secret",
        }
    }
    wheel = built_artifact("wheel", "demo.whl")
    sdist = built_artifact("sdist", "demo.tar.gz")
    mocker.patch(
        "apigateway.biz.sdk.publishers.pypi.SimplePypiRegistry.search",
        side_effect=[
            SimpleNamespace(url="https://cdn.example.net/demo.whl"),
            SimpleNamespace(url="https://cdn.example.net/demo.tar.gz"),
        ],
    )
    remote = mocker.patch(
        "apigateway.biz.sdk.publishers.pypi.remote_sha256",
        side_effect=[(wheel.sha256, wheel.size), (sdist.sha256, sdist.size)],
    )

    assert len(publish_native("python", [wheel, sdist], python_config)) == 2
    assert all(call.kwargs["username"] == "" for call in remote.call_args_list)
    assert all(call.kwargs["password"] == "" for call in remote.call_args_list)


def test_pypi_remote_conflict_is_rejected(mocker, built_artifact, python_config, settings):
    settings.PYPI_MIRRORS_CONFIG = {
        "default": {"index_url": "https://repo/simple", "repository_url": "https://repo/upload"}
    }
    wheel = built_artifact("wheel", "demo.whl")
    sdist = built_artifact("sdist", "demo.tar.gz")
    mocker.patch(
        "apigateway.biz.sdk.publishers.pypi.SimplePypiRegistry.search",
        return_value=SimpleNamespace(url="https://repo/demo.whl"),
    )
    mocker.patch("apigateway.biz.sdk.publishers.pypi.remote_sha256", return_value=("bad", wheel.size))

    with pytest.raises(SDKArtifactConflict):
        publish_native("python", [wheel, sdist], python_config)


def test_publisher_timeout_is_sanitized(mocker, built_artifact, python_config, settings):
    settings.PYPI_MIRRORS_CONFIG = {
        "default": {
            "index_url": "https://repo/simple",
            "repository_url": "https://repo/upload",
            "password": "secret",
        }
    }
    mocker.patch("apigateway.biz.sdk.publishers.pypi.SimplePypiRegistry.search", return_value=None)
    mocker.patch(
        "apigateway.biz.sdk.publishers.common.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["twine"], 1),
    )

    with pytest.raises(SDKGenerateError) as exc_info:
        publish_native(
            "python",
            [built_artifact("wheel", "demo.whl"), built_artifact("sdist", "demo.tar.gz")],
            python_config,
        )

    assert exc_info.value.code == "native_publish_failed"
    assert exc_info.value.retryable is True
    assert "secret" not in str(exc_info.value)


def test_pypi_failure_redacts_credentials_and_authorization(mocker, built_artifact, python_config, settings):
    settings.PYPI_MIRRORS_CONFIG = {
        "default": {
            "index_url": "https://repo/simple",
            "repository_url": "https://repo/upload",
            "username": "sdk-user",
            "password": "sdk-password",
        }
    }
    mocker.patch("apigateway.biz.sdk.publishers.pypi.SimplePypiRegistry.search", return_value=None)
    mocker.patch(
        "apigateway.biz.sdk.publishers.common.subprocess.run",
        return_value=subprocess.CompletedProcess(
            [],
            2,
            "",
            "Authorization: Bearer bearer-token password=sdk-password https://sdk-user:sdk-password@repo/upload",
        ),
    )

    with pytest.raises(SDKGenerateError) as exc_info:
        publish_native(
            "python",
            [built_artifact("wheel", "demo.whl"), built_artifact("sdist", "demo.tar.gz")],
            python_config,
        )

    message = str(exc_info.value)
    assert "sdk-password" not in message
    assert "bearer-token" not in message
    assert "sdk-user:" not in message
