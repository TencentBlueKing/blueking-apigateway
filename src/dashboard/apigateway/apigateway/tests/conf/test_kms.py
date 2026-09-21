# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import base64
import builtins
import json
import os
import runpy
import traceback
from urllib.parse import unquote, urlsplit

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from django.core.exceptions import ImproperlyConfigured

from apigateway.common.env import Env
from apigateway.conf import default, kms


@pytest.fixture(scope="module")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def credentials():
    return {
        "bkapp_id_secret": {
            "default": {"app_code": "kms-app", "app_secret": "kms-app-secret"},
            "bk_apigw_test": {"app_code": "kms-test", "app_secret": "kms-test-secret"},
        },
        "mysql": {
            "apigw": {"username": "db-user", "password": "$literal@:/密码"},
            "esb": {"username": "esb-user", "password": "esb-password"},
        },
        "redis": {"default": {"password": "redis@:密码"}},
        "etcd": {"default": {"username": "etcd-user", "password": "etcd-password"}},
        "rabbitmq": {"default": {"username": "rabbit-user", "password": "rabbit-password"}},
        "bkrepo": {
            "default": {"username": "generic-user", "password": "generic-password"},
            "pypi": {"username": "pypi-user", "password": "pypi-password"},
            "maven": {"username": "maven-user", "password": "maven-password"},
        },
        "encryption": {"encryptKey": "encryption-key"},
    }


@pytest.fixture
def envelope(monkeypatch, tmp_path, private_key):
    path = tmp_path / "envelope"
    monkeypatch.setattr(kms, "KMS_ENVELOPE_PATH", path)
    monkeypatch.setenv("ENABLE_KMS", "True")
    monkeypatch.setenv("ENABLE_MULTI_TENANT_MODE", "False")
    monkeypatch.setenv("BK_CRYPTO_TYPE", "APIGW_CUSTOM")
    for name in (
        "BK_APIGW_RABBITMQ_HOST",
        "BKREPO_ENDPOINT_URL",
        "DEFAULT_PYPI_REPOSITORY_URL",
        "DEFAULT_PYPI_INDEX_URL",
        "DEFAULT_MAVEN_REPOSITORY_URL",
    ):
        monkeypatch.setenv(name, "")
    pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    monkeypatch.setenv("BK_APIGATEWAY_KMS_PRIVATE_KEY", base64.b64encode(pem).decode())

    def write(payload):
        plaintext = payload if isinstance(payload, str) else json.dumps(payload)
        key, iv = os.urandom(16), os.urandom(16)
        encryptor = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
        ciphertext = iv + encryptor.update(plaintext.encode()) + encryptor.finalize()
        encrypted_key = private_key.public_key().encrypt(
            key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        data = {
            "asymmetric_type": "RSA",
            "symmetric_type": "AES",
            "symmetric_mode": "CTR",
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        path.write_text(base64.b64encode(json.dumps(data).encode()).decode() + "\n")
        return path

    return write


@pytest.mark.parametrize("flag", [None, "false", "False", "0"])
def test_disabled_keeps_original_env_without_loading_sdk(monkeypatch, flag):
    if flag is None:
        monkeypatch.delenv("ENABLE_KMS", raising=False)
    else:
        monkeypatch.setenv("ENABLE_KMS", flag)
    monkeypatch.setenv("BK_APP_SECRET", "legacy-secret")
    original_import = builtins.__import__

    def reject_sdk(name, *args, **kwargs):
        if name == "bk_kms":
            pytest.fail("disabled KMS imported the SDK")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_sdk)
    env = kms.get_env()
    assert type(env) is Env
    assert env.str("BK_APP_SECRET") == "legacy-secret"


def test_real_envelope_overrides_settings_without_mutating_environment(monkeypatch, envelope, credentials):
    envelope(credentials)
    monkeypatch.setenv("BK_APP_SECRET", "legacy-app-secret")
    monkeypatch.setenv("SECRET_KEY", "legacy-django-secret")
    monkeypatch.setenv("AI_API_KEY", "legacy-ai-key")
    monkeypatch.setenv("BK_APIGW_DATABASE_HOST", "mysql.example")
    before = dict(os.environ)
    settings = runpy.run_path(default.__file__)
    assert settings["BK_APP_CODE"] == "kms-app"
    assert settings["BK_APP_SECRET"] == "kms-app-secret"
    assert settings["SECRET_KEY"] == "legacy-django-secret"
    assert settings["AI_API_KEY"] == "legacy-ai-key"
    assert settings["DEFAULT_TEST_APP"] == {"bk_app_code": "kms-test", "bk_app_secret": "kms-test-secret"}
    assert settings["DATABASES"]["default"]["USER"] == "db-user"
    assert settings["DATABASES"]["default"]["PASSWORD"] == "$literal@:/密码"
    assert settings["DATABASES"]["default"]["HOST"] == "mysql.example"
    assert settings["DATABASES"]["bkcore"]["PASSWORD"] == "esb-password"
    assert settings["DEFAULT_REDIS_CONFIG"]["password"] == "redis@:密码"
    assert "redis%40%3A%E5%AF%86%E7%A0%81@" in settings["CELERY_BROKER_URL"]
    assert settings["ETCD_CONFIG"]["user"] == "etcd-user"
    assert settings["ETCD_CONFIG"]["password"] == "etcd-password"
    assert settings["JWT_CRYPTO_KEY"] == settings["LOG_LINK_SECRET"] == "encryption-key"
    assert dict(os.environ) == before


@pytest.mark.parametrize("bad_value", [None, "", "   ", 42, {}, []])
def test_missing_or_invalid_credential_never_falls_back(monkeypatch, envelope, credentials, bad_value):
    credentials["mysql"]["apigw"]["password"] = bad_value
    envelope(credentials)
    monkeypatch.setenv("BK_APIGW_DATABASE_PASSWORD", "old-password")
    with pytest.raises(ImproperlyConfigured, match=r"mysql.apigw.password"):
        kms.get_env()


def test_multi_tenant_does_not_require_esb(envelope, credentials, monkeypatch):
    del credentials["mysql"]["esb"]
    envelope(credentials)
    with pytest.raises(ImproperlyConfigured, match=r"mysql.esb"):
        kms.get_env()
    monkeypatch.setenv("ENABLE_MULTI_TENANT_MODE", "true")
    assert kms.get_env().str("BK_APIGW_DATABASE_USER") == "db-user"


@pytest.mark.parametrize(
    ("setting", "group", "instance", "username", "password"),
    [
        ("BKREPO_ENDPOINT_URL", "bkrepo", "default", "BKREPO_USERNAME", "BKREPO_PASSWORD"),
        ("DEFAULT_PYPI_REPOSITORY_URL", "bkrepo", "pypi", "DEFAULT_PYPI_USERNAME", "DEFAULT_PYPI_PASSWORD"),
        ("DEFAULT_MAVEN_REPOSITORY_URL", "bkrepo", "maven", "DEFAULT_MAVEN_USERNAME", "DEFAULT_MAVEN_PASSWORD"),
        ("BK_APIGW_RABBITMQ_HOST", "rabbitmq", "default", "BK_APIGW_RABBITMQ_USER", "BK_APIGW_RABBITMQ_PASSWORD"),
    ],
)
def test_configured_stores_require_their_own_account(
    monkeypatch, envelope, credentials, setting, group, instance, username, password
):
    monkeypatch.setenv(setting, "configured.example")
    envelope(credentials)
    env = kms.get_env()
    assert env.str(username) == credentials[group][instance]["username"]
    assert env.str(password) == credentials[group][instance]["password"]
    del credentials[group][instance]
    envelope(credentials)
    with pytest.raises(ImproperlyConfigured, match=group):
        kms.get_env()


@pytest.mark.parametrize("payload", ["not-json-sensitive-value", [], None, {}])
def test_invalid_plaintext_fails_without_leaking_values(envelope, payload):
    envelope(payload)
    with pytest.raises(ImproperlyConfigured) as exc:
        kms.get_env()
    assert "not-json-sensitive-value" not in "".join(traceback.format_exception(exc.value))


@pytest.mark.parametrize("failure", ["missing-key", "empty-key", "missing-file", "bad-envelope"])
def test_invalid_inputs_block_startup(monkeypatch, envelope, credentials, failure):
    path = envelope(credentials)
    if failure == "missing-key":
        monkeypatch.delenv("BK_APIGATEWAY_KMS_PRIVATE_KEY")
    elif failure == "empty-key":
        monkeypatch.setenv("BK_APIGATEWAY_KMS_PRIVATE_KEY", " ")
    elif failure == "missing-file":
        path.unlink()
    else:
        path.write_text("bad-envelope-sensitive-value")
    with pytest.raises(ImproperlyConfigured) as exc:
        kms.get_env()
    assert "bad-envelope-sensitive-value" not in "".join(traceback.format_exception(exc.value))


@pytest.mark.parametrize("rabbitmq", [False, True])
def test_kms_passwords_survive_broker_url_encoding(monkeypatch, envelope, credentials, rabbitmq):
    password = "p@ss:/?#%密码"
    credentials["redis"]["default"]["password"] = password
    if rabbitmq:
        monkeypatch.setenv("BK_APIGW_RABBITMQ_HOST", "rabbit.example")
        monkeypatch.setenv("BK_APIGW_RABBITMQ_PORT", "5672")
        monkeypatch.setenv("BK_APIGW_RABBITMQ_VHOST", "apigw")
        credentials["rabbitmq"]["default"] = {"username": "user@:/", "password": password}
    envelope(credentials)
    settings = runpy.run_path(default.__file__)
    broker = urlsplit(settings["CELERY_BROKER_URL"])
    assert unquote(broker.password) == password
    assert unquote(urlsplit(settings["CELERY_RESULT_BACKEND"]).password) == password
    if rabbitmq:
        assert unquote(broker.username) == "user@:/"
        assert broker.hostname == "rabbit.example"


def test_non_legacy_encryption_requires_its_key(monkeypatch, envelope, credentials):
    monkeypatch.setenv("BK_CRYPTO_TYPE", "CLASSIC")
    envelope(credentials)
    with pytest.raises(ImproperlyConfigured, match="encryption"):
        kms.get_env()
    credentials["encryption"]["bkkrillEncryptSecretKey"] = "krill-key"
    envelope(credentials)
    assert kms.get_env().str("BKKRILL_ENCRYPT_SECRET_KEY") == "krill-key"


def test_disabled_stores_need_no_credentials(envelope, credentials):
    del credentials["rabbitmq"]
    del credentials["bkrepo"]
    envelope(credentials)
    assert kms.get_env().str("BK_APP_CODE") == "kms-app"


def test_literal_app_secret_is_preserved_in_existing_defaults(envelope, credentials, monkeypatch):
    credentials["bkapp_id_secret"]["default"]["app_secret"] = "$kms-literal-app-secret"
    for name in ("SECRET_KEY", "AI_APP_SECRET"):
        monkeypatch.delenv(name, raising=False)
    envelope(credentials)
    settings = runpy.run_path(default.__file__)
    assert settings["BK_APP_SECRET"] == "$kms-literal-app-secret"
    assert settings["SECRET_KEY"] == "$kms-literal-app-secret"
    assert settings["AI_APP_SECRET"] == "$kms-literal-app-secret"
