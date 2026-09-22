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
"""Load deployment credentials before settings and derived connection configs."""

import json
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from apigateway.common.env import Env

KMS_ENVELOPE_PATH = Path("/etc/secrets/bk-apigateway-kms")


class _KMSEnv(Env):
    def __init__(self, credentials: dict[str, str]):
        super().__init__()
        self._credentials = credentials

    def get_value(self, var, cast=None, default=Env.NOTSET, parse_default=False):
        if var in self._credentials:
            # Credentials are literal strings, including leading '$'. Do not let
            # django-environ interpret them as references to other variables.
            return self.parse_value(self._credentials[var], cast)
        if var not in self.ENVIRON and default is not self.NOTSET:
            # Existing settings also pass decrypted values as defaults, e.g.
            # SECRET_KEY defaults to BK_APP_SECRET. These must stay literal too.
            return self.parse_value(default, cast) if parse_default and default is not None else default
        return super().get_value(var, cast=cast, default=default, parse_default=parse_default)


def _credential_bindings(env: Env) -> dict[str, tuple[str, ...]]:
    bindings = {
        "BK_APP_CODE": ("bkapp_id_secret", "default", "app_code"),
        "BK_APP_SECRET": ("bkapp_id_secret", "default", "app_secret"),
        "DEFAULT_TEST_APP_CODE": ("bkapp_id_secret", "bk_apigw_test", "app_code"),
        "DEFAULT_TEST_APP_SECRET": ("bkapp_id_secret", "bk_apigw_test", "app_secret"),
        "BK_APIGW_DATABASE_USER": ("mysql", "apigw", "username"),
        "BK_APIGW_DATABASE_PASSWORD": ("mysql", "apigw", "password"),
        "BK_APIGW_REDIS_PASSWORD": ("redis", "default", "password"),
        "BK_ETCD_USER": ("etcd", "default", "username"),
        "BK_ETCD_PASSWORD": ("etcd", "default", "password"),
        "ENCRYPT_KEY": ("encryption", "encryptKey"),
    }
    if not env.bool("ENABLE_MULTI_TENANT_MODE", False):
        bindings.update(
            {
                "BK_ESB_DATABASE_USER": ("mysql", "esb", "username"),
                "BK_ESB_DATABASE_PASSWORD": ("mysql", "esb", "password"),
            }
        )
    if env.str("BK_APIGW_RABBITMQ_HOST", ""):
        bindings.update(
            {
                "BK_APIGW_RABBITMQ_USER": ("rabbitmq", "default", "username"),
                "BK_APIGW_RABBITMQ_PASSWORD": ("rabbitmq", "default", "password"),
            }
        )
    if env.str("BKREPO_ENDPOINT_URL", ""):
        bindings.update(
            {
                "BKREPO_USERNAME": ("bkrepo", "default", "username"),
                "BKREPO_PASSWORD": ("bkrepo", "default", "password"),
            }
        )
    if env.str("DEFAULT_PYPI_REPOSITORY_URL", "") or env.str("DEFAULT_PYPI_INDEX_URL", ""):
        bindings.update(
            {
                "DEFAULT_PYPI_USERNAME": ("bkrepo", "pypi", "username"),
                "DEFAULT_PYPI_PASSWORD": ("bkrepo", "pypi", "password"),
            }
        )
    if env.str("DEFAULT_MAVEN_REPOSITORY_URL", ""):
        bindings.update(
            {
                "DEFAULT_MAVEN_USERNAME": ("bkrepo", "maven", "username"),
                "DEFAULT_MAVEN_PASSWORD": ("bkrepo", "maven", "password"),
            }
        )
    if env.str("BK_CRYPTO_TYPE", "APIGW_CUSTOM") != "APIGW_CUSTOM":
        bindings["BKKRILL_ENCRYPT_SECRET_KEY"] = ("encryption", "bkkrillEncryptSecretKey")
    return bindings


def is_kms_enabled() -> bool:
    return os.environ.get("ENABLE_KMS") in ("true", "True")


def get_env() -> Env:
    """Return the original env when disabled; fail closed for required KMS fields."""
    env = Env()
    if not is_kms_enabled():
        return env

    private_key = os.environ.get("BK_APIGATEWAY_KMS_PRIVATE_KEY", "").strip()
    if not private_key:
        raise ImproperlyConfigured("KMS requires BK_APIGATEWAY_KMS_PRIVATE_KEY")

    try:
        from bk_kms import CryptoError, decrypt  # noqa: PLC0415 -- disabled KMS must not import the SDK
    except ImportError:
        raise ImproperlyConfigured("KMS requires the bk-kms-sdk package") from None

    try:
        envelope = KMS_ENVELOPE_PATH.read_text(encoding="utf-8").strip()
        credentials = json.loads(decrypt(envelope=envelope, private_key=private_key))
    except OSError, UnicodeError, ValueError, CryptoError:
        # Do not propagate SDK/JSON exceptions that could expose payload values.
        raise ImproperlyConfigured("Unable to read or decrypt the KMS credential envelope") from None

    values = {}
    for name, path in _credential_bindings(env).items():
        value = credentials
        for part in path:
            value = value.get(part) if isinstance(value, dict) else None
        if not isinstance(value, str) or not value.strip():
            raise ImproperlyConfigured(f"KMS requires a non-empty string at {'.'.join(path)}")
        values[name] = value
    return _KMSEnv(values)
