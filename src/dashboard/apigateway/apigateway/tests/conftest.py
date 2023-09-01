# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import json
import tempfile
import uuid
from copy import deepcopy
from functools import partial

import fakeredis
import pytest
from celery import shared_task
from ddf import G
from django.contrib.auth import get_user_model
from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory as DRFAPIRequestFactory

from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginStyleEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm, PluginType
from apigateway.apps.support.models import APISDK, ResourceDoc
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.constants import (
    APIHostingTypeEnum,
    ProxyTypeEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusTypeEnum,
)
from apigateway.core.models import (
    Backend,
    BackendConfig,
    Gateway,
    MicroGateway,
    PublishEvent,
    Release,
    ReleasedResource,
    ReleaseHistory,
    Resource,
    ResourceVersion,
    Schema,
    SslCertificate,
    SslCertificateBinding,
    Stage,
)
from apigateway.schema import instances
from apigateway.schema.data.meta_schema import init_meta_schemas
from apigateway.tests.utils.testing import dummy_time, get_response_json
from apigateway.utils.redis_utils import REDIS_CLIENTS, get_default_redis_client

UserModel = get_user_model()

FAKE_USERNAME = "admin"


# pytest fixtures


def pytest_sessionstart(session):
    # pytest-django 4.3.0, https://pytest-django.readthedocs.io/en/latest/helpers.html
    # databases defaults to only the `default` database.
    # Error:
    #   Add 'bkcore' to pytest_django.fixtures._django_db_helper.<locals>.PytestDjangoTestCase.databases
    #   to ensure proper test isolation and silence this failure
    from django.test import TestCase

    TestCase.multi_db = True
    TestCase.databases = "__all__"


class APIRequestFactory(DRFAPIRequestFactory):
    def request(self, *args, **kwargs):
        request = super().request(*args, **kwargs)
        request.user = UserModel(username=FAKE_USERNAME, is_superuser=True)
        return request


@pytest.fixture(scope="class")
def request_factory():
    return APIRequestFactory()


# class FakeToken:
#     access_token: str = "access_token"


# class FakeUser:
#     is_active: bool = True
#     username: str = "admin"
#     is_authenticated: bool = True
#     token = FakeToken


@pytest.fixture
def fake_admin_user(mocker):
    return mocker.MagicMock(
        is_active=True,
        username="admin",
        is_authenticated=True,
        is_anonymous=False,
        is_superuser=True,
        token=mocker.MagicMock(access_token="access_token"),
    )


@pytest.fixture
def fake_anonymous_user(mocker):
    return mocker.MagicMock(
        is_active=True,
        username="test",
        is_authenticated=False,
        is_anonymous=True,
        is_superuser=False,
    )


@pytest.fixture
def fake_request(request_factory):
    request = request_factory.get("")

    return request


@pytest.fixture
def fake_gateway(faker):
    gateway = G(
        Gateway,
        name=faker.pystr(),
        _maintainers=FAKE_USERNAME,
        status=1,
        is_public=True,
        hosting_type=0,
    )

    GatewayAuthContext().save(gateway.pk, {})

    return gateway


@pytest.fixture()
def fake_gateway_for_micro_gateway(fake_gateway):
    fake_gateway.hosting_type = APIHostingTypeEnum.MICRO.value
    fake_gateway.save()

    return fake_gateway


@pytest.fixture
def fake_stage(fake_gateway, faker):
    return G(Stage, gateway=fake_gateway, status=1, name=faker.pystr(), description=faker.bothify("????????"))


@pytest.fixture
def fake_backend(fake_gateway, fake_stage, faker):
    backend = G(
        Backend,
        gateway=fake_gateway,
        name=faker.pystr(),
    )

    G(
        BackendConfig,
        gateway=fake_gateway,
        stage=fake_stage,
        backend=backend,
        config={
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
        },
    )

    return backend


@pytest.fixture
def fake_resource(faker, fake_gateway):
    resource = G(
        Resource,
        api=fake_gateway,
        name=faker.color_name(),
        method=faker.http_method(),
        path=faker.uri_path(),
    )
    ResourceHandler().save_auth_config(
        resource.id,
        {
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        },
    )
    ResourceHandler().save_proxy_config(
        resource,
        ProxyTypeEnum.HTTP.value,
        {
            "method": faker.http_method(),
            "path": faker.uri_path(),
            "match_subpath": False,
            "timeout": faker.random_int(),
            "upstreams": {
                "loadbalance": "roundrobin",
                "hosts": [{"host": f"http://{faker.domain_name()}", "weight": 100}],
            },
            "transform_headers": {},
        },
    )
    return resource


@pytest.fixture
def fake_resource1(faker, fake_resource):
    resource = deepcopy(fake_resource)
    resource.pk = None
    resource.name = faker.bothify("?????")
    resource.save()
    ResourceHandler().save_auth_config(
        resource.id,
        {
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        },
    )
    return resource


@pytest.fixture
def fake_resource2(faker, fake_resource):
    resource = deepcopy(fake_resource)
    resource.pk = None
    resource.name = faker.bothify("?????")
    resource.save()
    ResourceHandler().save_auth_config(resource.id, {})
    return resource


@pytest.fixture
def fake_micro_gateway(fake_gateway_for_micro_gateway, faker):
    gateway = G(
        MicroGateway,
        gateway=fake_gateway_for_micro_gateway,
        name=faker.color_name(),
        is_shared=False,
        _config=json.dumps(
            {
                "bcs": {
                    "project_id": faker.color_name(),
                    "project_name": faker.color_name(),
                    "cluster_id": faker.color_name(),
                    "namespace": faker.color_name(),
                    "chart_version": "1.0.0",
                    "release_name": faker.color_name(),
                },
                "http": {
                    "http_url": f"http://{faker.domain_name()}",
                },
                "jwt_auth": {
                    "secret_key": faker.password(),
                },
            }
        ),
    )
    return gateway


@pytest.fixture
def fake_edge_gateway(fake_micro_gateway, fake_stage):
    """专享网关"""
    fake_stage.micro_gateway = fake_micro_gateway
    fake_stage.save()

    return fake_micro_gateway


@pytest.fixture
def fake_shared_gateway(fake_micro_gateway, settings):
    """共享网关"""
    gateway = G(
        MicroGateway,
        gateway=fake_micro_gateway.gateway,
        name=fake_micro_gateway.name,
        is_shared=True,
        _config=fake_micro_gateway._config,
    )

    settings.DEFAULT_MICRO_GATEWAY_ID = str(gateway.id)
    return gateway


@pytest.fixture
def fake_resource_version(faker, fake_gateway, fake_resource1, fake_resource2):
    resource_version = G(ResourceVersion, gateway=fake_gateway, name=faker.pystr(), version=faker.pystr())
    resource_version.data = ResourceVersionHandler.make_version(fake_gateway)
    resource_version.save()
    return resource_version


@pytest.fixture
def fake_release(fake_gateway, fake_stage, fake_resource_version):
    return G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)


@pytest.fixture
def fake_release_history(fake_gateway, fake_stage, fake_resource_version):
    return G(
        ReleaseHistory,
        gateway=fake_gateway,
        stage=fake_stage,
        resource_version=fake_resource_version,
        created_time=dummy_time.time,
    )


@pytest.fixture
def fake_publish_event(fake_release_history):
    return G(
        PublishEvent,
        publish=fake_release_history,
        name=PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value,
        status=PublishEventStatusTypeEnum.DOING.value,
        created_time=dummy_time.time,
    )


@pytest.fixture
def fake_released_resource(fake_gateway, fake_resource1, fake_resource_version, fake_release):
    resource_id_to_data = {item["id"]: item for item in fake_resource_version.data}
    return G(
        ReleasedResource,
        gateway=fake_gateway,
        resource_version_id=fake_resource_version.id,
        resource_id=fake_resource1.id,
        resource_name=fake_resource1.name,
        resource_method=fake_resource1.method,
        resource_path=fake_resource1.path,
        data=resource_id_to_data[fake_resource1.id],
    )


@pytest.fixture
def api_factory():
    return partial(G, Gateway, _maintainers=FAKE_USERNAME)


@pytest.fixture(autouse=True)
def meta_schemas(db):
    schemas = init_meta_schemas()
    for s in schemas:
        Schema.objects.update_or_create(
            name=s.name,
            type=s.type,
            version=s.version,
            defaults={
                "schema": s.schema,
                "description": s.description,
                "example": s.example,
            },
        )


@pytest.fixture
def unique_id():
    return uuid.uuid4().hex


@pytest.fixture
def unique_gateway_name(unique_id):
    return f"a{unique_id[:19]}"


@pytest.fixture
def unique_backend_service_name(unique_id):
    return f"a{unique_id[:20]}".lower()


@pytest.fixture
def unique_stage_item_name(unique_id):
    return f"a{unique_id[:19]}".lower()


@pytest.fixture
def fake_tgz_file(faker):
    fp = tempfile.TemporaryFile()
    fp.write(faker.tar(compression="gz"))
    fp.seek(0)
    return fp


@pytest.fixture
def fake_zip_file(faker):
    fp = tempfile.TemporaryFile()
    fp.write(faker.zip())
    fp.seek(0)
    return fp


@pytest.fixture
def fake_text_file(faker):
    fp = tempfile.TemporaryFile()
    fp.write(faker.binary(length=64))
    fp.seek(0)
    return fp


@pytest.fixture
def celery_task_eager_mode(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture()
def fake_sdk(fake_gateway, fake_resource_version):
    return G(
        APISDK,
        gateway=fake_gateway,
        resource_version=fake_resource_version,
        language="magic",
        is_recommended=True,
        _config="{}",
    )


@pytest.fixture()
def request_to_view():
    def fn(request, view_name, path_params=None):
        path = reverse(view_name, kwargs=path_params)
        resolved = resolve(path)
        return resolved.func(request, *resolved.args, **resolved.kwargs)

    return fn


@pytest.fixture()
def request_view(request_factory):
    def fn(method, view_name, path_params=None, gateway=None, user=None, **kwargs):
        handler = getattr(request_factory, method.lower())
        request = handler(path="", **kwargs)
        request.gateway = gateway
        if user is not None:
            request.user = user
        path = reverse(view_name, kwargs=path_params)
        resolved = resolve(path)
        response = resolved.func(request, *resolved.args, **resolved.kwargs)
        response.json = partial(get_response_json, response)

        return response

    return fn


class FakeRedis(fakeredis.FakeRedis):
    REDIS_PREFIX: str

    def __init__(self, connection_pool=None, *args, **kwargs):
        super(FakeRedis, self).__init__(*args, **kwargs)

    def execute_command(self, command, *args, **kwargs):
        has_prefix = len(args) == 0

        for i in args:
            # test all redis command has key prefix
            if isinstance(i, str) and i.startswith(self.REDIS_PREFIX):
                has_prefix = True

        if not has_prefix:
            raise KeyError("Redis prefix not found")

        return super(FakeRedis, self).execute_command(command, *args, **kwargs)


@pytest.fixture(autouse=True)
def patch_redis(mocker, settings):
    class PatchedRedis(FakeRedis):
        REDIS_PREFIX = settings.REDIS_PREFIX

    REDIS_CLIENTS.clear()
    mocker.patch("redis.Redis", PatchedRedis)


@pytest.fixture(autouse=True)
def patch_channel_patch(settings):
    settings.APIGW_REVERSION_UPDATE_CHANNEL_KEY = (
        f"{settings.REDIS_PREFIX}{settings.APIGW_REVERSION_UPDATE_CHANNEL_KEY}"
    )


@pytest.fixture
def default_redis():
    return get_default_redis_client()


@pytest.fixture
def skip_view_permissions_check(mocker):
    mocker.patch("rest_framework.views.APIView.check_permissions")


@pytest.fixture
def micro_gateway_schema():
    return Schema.objects.get(name=instances.SCHEMA_NAME_MICRO_GATEWAY)


@pytest.fixture(autouse=True)
def mock_rest_framework_settings(settings):
    settings.REST_FRAMEWORK.update({"DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S"})


@shared_task(name="testing.mock")
def celery_mock_task_for_testing(celery_task_mocker=None, *args, **kwargs):
    if celery_task_mocker:
        celery_task_mocker(*args, **kwargs)


@pytest.fixture()
def celery_mock_task():
    return celery_mock_task_for_testing


@pytest.fixture
def fake_node_data(unique_stage_item_name):
    return {
        "name": unique_stage_item_name,
        "type": "node",
        "description": "this is a test",
        "config": {
            "nodes": [
                {
                    "host": "1.0.0.1:8000",
                    "weight": 100,
                },
            ]
        },
    }


@pytest.fixture
def fake_ssl_certificate(fake_gateway):
    return G(SslCertificate, api=fake_gateway)


@pytest.fixture
def fake_ssl_certificate_binding(fake_ssl_certificate):
    stage = G(Stage, gateway=fake_ssl_certificate.api)
    return G(
        SslCertificateBinding,
        api=fake_ssl_certificate.api,
        scope_type="stage",
        scope_id=stage.id,
        ssl_certificate=fake_ssl_certificate,
    )


@pytest.fixture()
def echo_plugin_type_schema():
    # apisix echo plugin schema
    return G(
        Schema,
        name="echo_schema",
        _schema=json.dumps(
            {
                "type": "object",
                "properties": {
                    "before_body": {"description": "body before the filter phase.", "type": "string"},
                    "body": {"description": "body to replace upstream response.", "type": "string"},
                    "after_body": {"description": "body after the modification of filter phase.", "type": "string"},
                    "headers": {
                        "description": "new headers for response",
                        "type": "object",
                        "minProperties": 1,
                    },
                },
                "anyOf": [
                    {"required": ["before_body"]},
                    {"required": ["body"]},
                    {"required": ["after_body"]},
                ],
                "minProperties": 1,
            }
        ),
    )


@pytest.fixture()
def echo_plugin_type(echo_plugin_type_schema):
    return G(
        PluginType,
        code="echo",
        name="echo",
        schema=echo_plugin_type_schema,
        is_public=True,
    )


@pytest.fixture()
def echo_plugin_default_form(echo_plugin_type):
    return G(
        PluginForm,
        language="",
        type=echo_plugin_type,
        config=None,
        style=PluginStyleEnum.RAW.value,
    )


@pytest.fixture()
def echo_plugin_en_form(echo_plugin_type):
    return G(
        PluginForm,
        language="en",
        type=echo_plugin_type,
        config=None,
        style=PluginStyleEnum.RAW.value,
    )


@pytest.fixture()
def echo_plugin(echo_plugin_type, fake_gateway, faker):
    return G(
        PluginConfig,
        gateway=fake_gateway,
        name="echo-plugin",
        type=echo_plugin_type,
        yaml=json.dumps(
            {
                faker.random_element(["before_body", "body", "after_body"]): faker.pystr(),
            }
        ),
    )


@pytest.fixture()
def echo_plugin_stage_binding(echo_plugin, fake_stage):
    return G(
        PluginBinding,
        gateway=echo_plugin.gateway,
        config=echo_plugin,
        scope_type=PluginBindingScopeEnum.STAGE.value,
        scope_id=fake_stage.pk,
    )


@pytest.fixture()
def echo_plugin_resource_binding(echo_plugin, fake_resource):
    return G(
        PluginBinding,
        gateway=echo_plugin.gateway,
        config=echo_plugin,
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id=fake_resource.pk,
    )


@pytest.fixture()
def clone_model():
    """Clone a django model"""

    def clone(model, **kwargs):
        new_model = deepcopy(model)
        new_model.pk = None

        for k, v in kwargs.items():
            setattr(new_model, k, v)

        new_model.save()
        return model._meta.model.objects.get(pk=new_model.pk)

    return clone


@pytest.fixture()
def fake_rsa_private_key():
    return """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEArkgtL4OVsDVSlns1n5EAqs908uDoQMoPJ+2i3o/ddKXRObaN
aVK42iLtfRaFiuQNKWKr5jNP18mBrMi0Sc7J85nzrc7UW5wVsXovTqTxcIo0/twI
LfAJbe1j900rw4F/7P69bHypKsyLg8aevmL+Pl0DPBh25x+pFeOHfIeOqLeXFA4x
/8nGjr9dHYZ/XXUGV4tozrUqiUzLYyyFieJ/r9ZrSf1FnUFRrUr4d9WQ3k8/SB0a
MHNyqJy92U2wjZkMS04fIngNwNk+AVYCyPnOCmbfBsYnfo5X9mARGWI5suoF5Gy3
6Tsc9mA718bbm1pYOsEv2zkfXPVB/8VTRFr4UQIDAQABAoIBAEbKUnBGRnr4bb9p
9HIH9/lpots0t6H5cQaK4+j7DrzezYlfuTjavPL91PFGQKAV2bLBvYkXtoqz8tQ4
AeMo96bXFb+3j1JWqAka1DRhkyBfQv9yaHAgW/QmxMAivHABHfEp189FI4Ga6+Bu
wPQcSaETLskuNr3Sgl+9t77BYRTuMXkCvKLiRpNUEXxkJz3zK9gpSD2Abk2dBEMX
E+2znefQC/FtFYW9GA9yH3WMk1znAQ80ru2GhqnL/6nWXiHd+iP95NQO7lgZPJYE
/dj+om7AaSEBzd20Y+OIL/wBr3ZdgoQMBHQyrTPcy/olNKtuAHJOg1Zvwh5kc+SD
1kw4dXECgYEA5CIBoM2rL6JgQc1PfopJJjmhw0ZY/G4NyWpjjDUDF+hTclvhmP+3
A9DTOZ3IU8liv0sf0zcjkomxgGuIwERKHNgRCukj31Faj3TCzzXjJWrdrbO7y7iZ
omWLY9QiDmm+WW0VnVZIMdrcJW618wIsE6WAYqvln59dIaTlpauIad8CgYEAw5Iv
v7nEBgBjNwFhKrvp9rQd4aFbfVRWkfQ2uwuioXxdvQW3l6l6eg4R0VG5I+ju0908
sHfutIjBX5vLjidq5qkhh0ykSSQkMzrkyrtlyp1ua6po9eDIzX5AFQ2wE1vRYebL
TwqXMubL6FY0p/eXoY45PwAirboRqUA37v2oQ88CgYA5MUVTOPyHrp+PH5ekU6rP
CHfDaul4L2cJbcCTL98cqUPyUZKXNtR9AmdR9Hp6duxopL7Pxu0GGbsERPE9smEa
JhjvsU8q90xK1qzYIdxWTxpQJ9UW16q8idSOLGp1TpFH/g8DKNRkm0fBoqW+zHac
Xkt3cTzZ7av9eUeRZxWF5QKBgQCnHgpTaShKgJZHcJRZcg4xVCSco8eMRz9apTcH
ip/EIoPvfC0wGhCgr9kl5xGvz+IVhN3RZgrCloG3c2fz51cAF9KgzSstnQaaCF9t
pckL5I9wzUO3qAevIY0c8H9fa3x2jkN5HXGqe3IO7Ws9hOM7mE7uuOzpSzDAUjH5
tSPOHQKBgQCkkUVo9aYWA01sBGrGRjEGDcZOzU7T4N76b0ITFtiXbOzZ20z2teI5
+wiLqAKsX44QvBN7szPUTAnewDysyuyRZs3BHkKAn3dTY07+dxeEhxyvrhpe/+Zy
HzV20y86NzieCckY3hZ48rUexloYPVn+9T4NgPL8SYUkSoTygOJZ8w==
-----END RSA PRIVATE KEY-----"""


@pytest.fixture()
def fake_rsa_public_key():
    return """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArkgtL4OVsDVSlns1n5EA
qs908uDoQMoPJ+2i3o/ddKXRObaNaVK42iLtfRaFiuQNKWKr5jNP18mBrMi0Sc7J
85nzrc7UW5wVsXovTqTxcIo0/twILfAJbe1j900rw4F/7P69bHypKsyLg8aevmL+
Pl0DPBh25x+pFeOHfIeOqLeXFA4x/8nGjr9dHYZ/XXUGV4tozrUqiUzLYyyFieJ/
r9ZrSf1FnUFRrUr4d9WQ3k8/SB0aMHNyqJy92U2wjZkMS04fIngNwNk+AVYCyPnO
CmbfBsYnfo5X9mARGWI5suoF5Gy36Tsc9mA718bbm1pYOsEv2zkfXPVB/8VTRFr4
UQIDAQAB
-----END PUBLIC KEY-----"""


@pytest.fixture
def fake_tls_cacert():
    return """-----BEGIN CERTIFICATE-----
MIIDDjCCAfYCCQDJqct/JR+xnTANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJD
TjETMBEGA1UECAwKR3VhbmcgRG9uZzESMBAGA1UEBwwJU2hlbiBaaGVuMREwDwYD
VQQKDAhCbHVla2luZzAeFw0yMjEyMTkwMzUxMThaFw0yMzAxMTgwMzUxMThaMEkx
CzAJBgNVBAYTAkNOMRMwEQYDVQQIDApHdWFuZyBEb25nMRIwEAYDVQQHDAlTaGVu
IFpoZW4xETAPBgNVBAoMCEJsdWVraW5nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
MIIBCgKCAQEAxw/MwDiFwDI5XCwWpUu29q5ULFeJ/agwaa93Tvk4W/kzeX0JcrPf
Eg77+MoZe0N9p0EElxB1wFXuz9Q6zfF9+FP5OEhQ6i/ZA/hLyTy05ohGBqoIV4+X
qew8cYDReWkak8XJkSkSEwZ14KeL9MBHigyuXb6kDcvwlzym13KULKHpICyKOam3
srFuwYfs3xXgImfkcVwPkU8Qu+fRjpSMOHmxJ7ZeYha5yaoBOxB63KGIyjTn7se7
qzQ7xwUWVJc+SKHyD5OqVOVTG0KfYO0Zxiqy3Ig+GeOQ+EvqvZuY0cJegdBFv1YY
9BN14kheymA0YPrqXy+l49uYwy7VzyeE4wIDAQABMA0GCSqGSIb3DQEBCwUAA4IB
AQCUv7Bh6giFw3zanEYWMvBasPRoave4vh6ONpqx9a7b7ERLPb3FW99+2CIicvYg
HF450hAoOfprCOy1icqpwxb4epZImlYXOfn5GBarI7TOrBb3J6hIOSmrai5ej8XW
F2Hs9wDj2OUV+duyrD4yjSYoMc0QBz9Ysf++9mNClcmiofc8uDPgIw5SDLbI/jyt
THsHTVzrpx3rXACc8sqYzX23jOEzxpCHMmuQ/n1GJ7reIR4ym2FpZSaE904gUIni
Ba4fi0pI9a4o7fADpyB/RVaEcUThKhujueInkEcK8vPLmwCSL4cepgt7v63PITcY
K3s6g+mRLT9+jRicv0yHGnl0
-----END CERTIFICATE-----"""


@pytest.fixture
def fake_tls_cert():
    return """-----BEGIN CERTIFICATE-----
MIIDKjCCAhICCQCnAH4ftfJ0jzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJD
TjETMBEGA1UECAwKR3VhbmcgRG9uZzESMBAGA1UEBwwJU2hlbiBaaGVuMREwDwYD
VQQKDAhCbHVla2luZzAeFw0yMjEyMTkwMzUzMDhaFw0yMzAxMTgwMzUzMDhaMGUx
CzAJBgNVBAYTAkNOMRMwEQYDVQQIDApHdWFuZyBEb25nMRIwEAYDVQQHDAlTaGVu
IFpoZW4xETAPBgNVBAoMCEJsdWVraW5nMRowGAYDVQQDDBFia2FwaS5leGFtcGxl
LmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKGuvyzagosT6XHx
LjnPGo/jpVAS7fCFXAarXIteC7WGkAADiHXB6XWbKnDtDx2N4Ubrqm6LsTLh2K/u
QLJI7SeOQOmt2Lm+C2FRorVhQ+HM7qKBDAajlFWuWL12vaFbDro5TlDe7uGXiOZy
ydCw/J9slCRhF6OPfAMl3xxj22HG/7Um5jyNK+txyuUFkR/wnpqDKstRzVmKQC3q
7XFvDd4ohh1ExumZeCrqr/JSzYKeMVjGnwJtvlhC/Qrhcq+j65Npg6I7jJLbzqvX
Rx/ufeqIsxF9nO+7/FEXESec37RRIj64EKQFZYXmoO/a7vMs9GDP6V1e5HQ+NcKS
/PzbuQsCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAL0NZnfp7Bo7RBelWDh23A1aQ
BGO8aVzhkQ58pqNhL4xmJ02G0CahoBwzcr3dk+dbY+ueNi0IQZ2Y6rw+EgFrJyEw
FQyhu15a54kEbMLuSCeLPtgRCMfEeJZZ/nNnPatLE5jhwdfzynBvjWG5U0LhTWYr
1NAldRcZo0GZtrPkQdsiLrWo8hBzTGrQQoNdKaK6qwf+LKMHMvvueH/B2TMPxXa3
RsNRePuY7fHa/b/sostvxUWhWK1GIx79lJBTzq08iJwYXk84IoPsMvwRfSNKVJce
UQpa4uSKycJVDzIx0qhgnyHKg5nGT1JV+chWE0rHbz8Hs0l0sy0Owv0IWibq2g==
-----END CERTIFICATE-----"""


@pytest.fixture
def fake_tls_key():
    return """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAoa6/LNqCixPpcfEuOc8aj+OlUBLt8IVcBqtci14LtYaQAAOI
dcHpdZsqcO0PHY3hRuuqbouxMuHYr+5AskjtJ45A6a3Yub4LYVGitWFD4czuooEM
BqOUVa5YvXa9oVsOujlOUN7u4ZeI5nLJ0LD8n2yUJGEXo498AyXfHGPbYcb/tSbm
PI0r63HK5QWRH/CemoMqy1HNWYpALertcW8N3iiGHUTG6Zl4Kuqv8lLNgp4xWMaf
Am2+WEL9CuFyr6Prk2mDojuMktvOq9dHH+596oizEX2c77v8URcRJ5zftFEiPrgQ
pAVlheag79ru8yz0YM/pXV7kdD41wpL8/Nu5CwIDAQABAoIBAQCX5zscJAvEKSgJ
8kOw8oCNMZ8OVUqR0Gm+pl8jXW940/0U1jzuDgqOgQLl6ANsi/FclWuhwsLwADp6
SEkmd9fAcylPoxLcp82/WFibOs/xJH4L1Vx8HFHwEgazswzEvW1fzxliZ6Fd9+Ya
RTyRQseF7Rhd+Y6hD9y+hGVTIgpqmHMywI6ZBNsIVZ1pCoKu3X2A/jdgFYo4TV2m
CMosfxvynH6m9yb0zaLWcRpj1a4YYxAdiXpVPeEvXuhCtgQFfA1BTZTDQcWiASpC
A/kWZN0B9k2rSqpuzu2+NPNgBrso/bahpcQ4REGGpdxbaC9CY34XwNcfkZfGO4Hm
AKyljsM5AoGBAM343rKRwjunYCsaeDK44uATKWCeZU4iMeVq5D7A/vOekO34EeFx
j0QfYhBuy9B85McdhpA8k/yL97Yv8gExQrfmi4eAOFK8mUQSAYSR+N9rhBxfZ83N
MhX52sc9jKfkolguT2YLzmbAuFUhNGohlVMn/oPMohx0jIZcPTY2sq9fAoGBAMjz
//xhWY36VYc7unfWbKQ2fDwHHDWEnwoLEG1VasZTuuVeLjHCE74TOcHMU+dF+Nec
7Y/T9wq20b7dGr8df1iU1iSsyPPZBG3O7n1GGCnbkxkueQ3Dl7rjb/yk6I+43KMx
TGpkSrp0vaknb2f7oJmapNsuDm+3NDkNxj4oBZHVAoGATA2z9U264ZoI+YF5lokM
RN7ubV2vXG1l7SdOBhnvSfdn3ma1+3+Z/fZ0mErA+UfUle1CDapAnoT0P5JukqAk
2ZDIPo1Kvsoi8a6QXuojciPaETvtMWGuN80dSmpgsHHMvDDFYpHDcc+BgPWUzAeA
gscGxJXf2g/y/325oHYL/pMCgYBZfqlbufNLUtiyYHxcEIfT3lwX08bRYt39eA35
01e5OeL7caU7DccDGMbZM2mOj1ASnlYCfxD/mYnx6cCWqsljJu3z6WuZheX+DXGT
Ixtx0NNDHLpW0ewKFG50YvEbyOWiXDs/CqlpPsKUyfZIpfzRS9jtsCZHxJyiaCsI
1YQdfQKBgCwlFizsm63tR4dBZRhg6uGwmEPubQtshdVtrSKW084kFFsw4fSNJejV
5H2rPBBrtS205FnnBClIRt+Wx+rKAZxaeJrE5Y+xE6sEoL7aCx/Pt+SjtNhq57i4
X2wViL+hl304B82EpeKdGjly2YtdRmBCekANPxS24315bU6fGvBr
-----END RSA PRIVATE KEY-----"""


@pytest.fixture
def mock_board(settings):
    settings.ESB_BOARD_CONFIGS = {
        "open": {
            "name": "open",
            "label": "Open",
            "has_sdk": True,
            "sdk_name": "blueking-component-open",
            "sdk_package_prefix": "blueking.component.open",
            "sdk_description": "access open apis",
            "sdk_doc_templates": {
                "python_sdk_usage_example": "test.md",
            },
        },
    }

    return "open"


@pytest.fixture
def fake_resource_doc(faker, fake_resource):
    return G(
        ResourceDoc,
        api=fake_resource.api,
        resource_id=fake_resource.id,
        language=faker.random_element(
            ["en", "zh"],
        ),
    )
