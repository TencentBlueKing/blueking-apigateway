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
import runpy

import pytest
from django.core.exceptions import ImproperlyConfigured

from apigateway.conf import default

pytestmark = pytest.mark.no_meta_schema


@pytest.fixture(autouse=True)
def redis_env(monkeypatch):
    monkeypatch.setenv("ENABLE_KMS", "False")
    monkeypatch.setenv("BK_APIGW_REDIS_PASSWORD", "p@ss")
    monkeypatch.setenv("BK_APIGW_REDIS_DB", "0")
    monkeypatch.setenv("BK_APIGW_REDIS_TLS_ENABLED", "False")
    for name in ("HOST", "PORT", "VHOST", "USER", "PASSWORD"):
        monkeypatch.setenv(f"BK_APIGW_RABBITMQ_{name}", "")


def enable_rabbitmq(monkeypatch):
    for name, value in {"HOST": "rabbit", "PORT": "5672", "VHOST": "v", "USER": "u", "PASSWORD": "p"}.items():
        monkeypatch.setenv(f"BK_APIGW_RABBITMQ_{name}", value)


@pytest.mark.parametrize(
    "env, match",
    [
        ({"BK_APIGW_REDIS_MODE": "standalone"}, "unsupported BK_APIGW_REDIS_MODE"),
        ({"BK_APIGW_REDIS_MODE": "sentinel", "BK_APIGW_REDIS_ADDRS": ""}, "BK_APIGW_REDIS_ADDRS is required"),
        ({"BK_APIGW_REDIS_MODE": "cluster", "BK_APIGW_REDIS_ADDRS": ""}, "BK_APIGW_REDIS_ADDRS is required"),
        (
            {"BK_APIGW_REDIS_MODE": "cluster", "BK_APIGW_REDIS_ADDRS": "n1:6379", "BK_APIGW_REDIS_DB": "1"},
            "only support db 0",
        ),
        ({"BK_APIGW_REDIS_MODE": "cluster", "BK_APIGW_REDIS_ADDRS": "n1:6379"}, "requires rabbitmq"),
    ],
)
def test_invalid_redis_config(monkeypatch, env, match):
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(ImproperlyConfigured, match=match):
        runpy.run_path(default.__file__)


def test_sentinel_celery_config(monkeypatch):
    monkeypatch.setenv("BK_APIGW_REDIS_MODE", "sentinel")
    monkeypatch.setenv("BK_APIGW_REDIS_ADDRS", "s1:26379, s2:26379")
    monkeypatch.setenv("BK_APIGW_REDIS_SENTINEL_PASSWORD", "sentinel-password")
    monkeypatch.setenv("BK_APIGW_REDIS_TLS_ENABLED", "True")
    monkeypatch.setenv("BK_APIGW_REDIS_SENTINEL_TLS_ENABLED", "False")

    settings = runpy.run_path(default.__file__)

    url = "sentinel://:p%40ss@s1:26379/0;sentinel://:p%40ss@s2:26379/0"
    assert settings["CELERY_BROKER_URL"] == settings["CELERY_RESULT_BACKEND"] == url
    options = settings["CELERY_BROKER_TRANSPORT_OPTIONS"]
    assert options["master_name"] == "mymaster"
    assert options["sentinel_kwargs"]["password"] == "sentinel-password"
    assert "ssl" not in options["sentinel_kwargs"]
    assert settings["CELERY_BROKER_USE_SSL"] == settings["CELERY_REDIS_BACKEND_USE_SSL"]
    assert settings["DEFAULT_REDIS_CONFIG"]["addrs"] == ["s1:26379", "s2:26379"]


def test_sentinel_with_rabbitmq_only_uses_sentinel_result_backend(monkeypatch):
    enable_rabbitmq(monkeypatch)
    monkeypatch.setenv("BK_APIGW_REDIS_MODE", "sentinel")
    monkeypatch.setenv("BK_APIGW_REDIS_ADDRS", "s1:26379")

    settings = runpy.run_path(default.__file__)

    assert settings["CELERY_BROKER_URL"].startswith("amqp://")
    assert settings["CELERY_RESULT_BACKEND"].startswith("sentinel://")
    assert "CELERY_BROKER_USE_SSL" not in settings


def test_cluster_with_rabbitmq(monkeypatch):
    enable_rabbitmq(monkeypatch)
    monkeypatch.setenv("BK_APIGW_REDIS_MODE", "cluster")
    monkeypatch.setenv("BK_APIGW_REDIS_ADDRS", "n1:6379,n2:6379")

    settings = runpy.run_path(default.__file__)

    assert settings["CELERY_BROKER_URL"].startswith("amqp://")
    assert settings["CELERY_RESULT_BACKEND"] is None
