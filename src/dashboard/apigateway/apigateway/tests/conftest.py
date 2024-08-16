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

import pytest
from celery import shared_task
from ddf import G
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory as DRFAPIRequestFactory

from apigateway.apps.openapi.models import OpenAPIResourceSchema
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginStyleEnum, PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm, PluginType
from apigateway.apps.support.models import GatewaySDK, ReleasedResourceDoc, ResourceDoc, ResourceDocVersion
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource.models import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.factories import SchemaFactory
from apigateway.core.constants import (
    ProxyTypeEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusTypeEnum,
    ResourceVersionSchemaEnum,
)
from apigateway.core.models import (
    Backend,
    BackendConfig,
    Gateway,
    MicroGateway,
    Proxy,
    PublishEvent,
    Release,
    ReleasedResource,
    ReleaseHistory,
    Resource,
    ResourceVersion,
    Schema,
    Stage,
)
from apigateway.schema import instances
from apigateway.schema.data.meta_schema import init_meta_schemas
from apigateway.tests.utils.testing import dummy_time, get_response_json
from apigateway.utils.yaml import yaml_dumps

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
        request.COOKIES[settings.BK_LOGIN_TICKET_KEY] = "access_token"
        return request


@pytest.fixture(scope="class")
def request_factory():
    return APIRequestFactory()


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
def fake_request(request_factory):
    return request_factory.get("")


@pytest.fixture
def fake_gateway(faker):
    gateway = G(
        Gateway,
        name=faker.pystr(),
        _maintainers=FAKE_USERNAME,
        status=1,
        is_public=True,
    )

    GatewayAuthContext().save(gateway.pk, {})

    return gateway


@pytest.fixture()
def fake_gateway_for_micro_gateway(fake_gateway):
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
def fake_grpc_backend(fake_gateway, fake_stage, faker):
    backend = G(Backend, gateway=fake_gateway, name=faker.pystr(), type="grpc")

    G(
        BackendConfig,
        gateway=fake_gateway,
        stage=fake_stage,
        backend=backend,
        config={
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "grpc", "host": "example.com:999", "weight": 100}],
        },
    )

    return backend


@pytest.fixture
def fake_default_backend(fake_gateway, fake_stage, faker):
    backend = G(
        Backend,
        gateway=fake_gateway,
        name="default",
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
def fake_resource(faker, fake_gateway, fake_backend):
    resource = G(
        Resource,
        gateway=fake_gateway,
        name=faker.color_name(),
        method=faker.http_method(),
        path=faker.uri_path(),
    )
    ResourceHandler.save_auth_config(
        resource.id,
        {
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        },
    )
    G(
        Proxy,
        type=ProxyTypeEnum.HTTP.value,
        resource=resource,
        backend=fake_backend,
        _config=json.dumps(
            {
                "method": faker.http_method(),
                "path": faker.uri_path(),
                "match_subpath": False,
                "timeout": faker.random_int(),
            }
        ),
        schema=SchemaFactory().get_proxy_schema(ProxyTypeEnum.HTTP.value),
    )

    return resource


@pytest.fixture
def fake_resource1(faker, fake_resource):
    resource = deepcopy(fake_resource)
    resource.pk = None
    resource.is_public = True
    resource.name = faker.bothify("?????")
    resource.save()

    ResourceHandler.save_auth_config(
        resource.id,
        {
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        },
    )

    proxy = deepcopy(Proxy.objects.get(resource_id=fake_resource.id))
    proxy.pk = None
    proxy.resource = resource
    proxy.save()

    return resource


@pytest.fixture
def fake_resource2(faker, fake_resource):
    resource = deepcopy(fake_resource)
    resource.pk = None
    resource.name = faker.bothify("?????")
    resource.save()

    ResourceHandler.save_auth_config(resource.id, {})

    proxy = deepcopy(Proxy.objects.get(resource_id=fake_resource.id))
    proxy.pk = None
    proxy.resource = resource
    proxy.save()

    return resource


@pytest.fixture
def fake_micro_gateway(fake_gateway_for_micro_gateway, faker):
    return G(
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
def fake_resource_schema(fake_gateway, fake_resource):
    return G(
        OpenAPIResourceSchema,
        resource=fake_resource,
        schema={
            "parameters": [
                {
                    "name": "userId",
                    "in": "path",
                    "description": "ID of User",
                    "required": True,
                    "type": "integer",
                    "format": "int64",
                }
            ],
        },
    )


@pytest.fixture
def fake_resource_schema_with_body(fake_gateway, fake_resource):
    return G(
        OpenAPIResourceSchema,
        resource=fake_resource,
        schema={
            "requestBody": {
                "description": "Update an existent pet in the store",
                "content": {
                    "application/json": {
                        "schema": {
                            "required": ["name", "photoUrls"],
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "format": "int64", "example": 10},
                                "name": {"type": "string", "example": "doggie"},
                                "status": {
                                    "type": "string",
                                    "description": "pet status in the store",
                                    "enum": ["available", "pending", "sold"],
                                },
                            },
                            "xml": {"name": "pet"},
                        }
                    }
                },
                "required": True,
            },
        },
    )


@pytest.fixture
def fake_resource_version_v2(faker, fake_gateway, fake_resource):
    resource_version = G(
        ResourceVersion,
        gateway=fake_gateway,
        name=faker.pystr(),
        version=faker.pystr(),
        schema_version=ResourceVersionSchemaEnum.V2.value,
    )
    resource_version.data = ResourceVersionHandler.make_version(fake_gateway)
    resource_version.save()
    return resource_version


@pytest.fixture
def fake_resource_version_v1(faker, fake_gateway, fake_resource):
    resource_version = G(
        ResourceVersion,
        gateway=fake_gateway,
        name=faker.pystr(),
        version=faker.pystr(),
        schema_version=ResourceVersionSchemaEnum.V1.value,
    )
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
def fake_publish_success_event(fake_release_history):
    return G(
        PublishEvent,
        publish=fake_release_history,
        name=PublishEventNameTypeEnum.LOAD_CONFIGURATION.value,
        status=PublishEventStatusTypeEnum.SUCCESS.value,
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
def fake_resource_doc1(fake_resource1):
    return G(ResourceDoc, gateway=fake_resource1.gateway, resource_id=fake_resource1.id)


@pytest.fixture
def fake_resource_doc2(fake_resource2):
    return G(ResourceDoc, gateway=fake_resource2.gateway, resource_id=fake_resource2.id)


@pytest.fixture
def fake_resource_doc_version(fake_gateway, fake_resource_version, fake_resource_doc1, fake_resource_doc2):
    resource_doc_version = G(ResourceDocVersion, gateway=fake_gateway, resource_version=fake_resource_version)
    resource_doc_version.data = ResourceDocVersion.objects.make_version(fake_gateway.id)
    resource_doc_version.save()
    return resource_doc_version


@pytest.fixture
def fake_released_resource_doc(fake_gateway, fake_resource_version, fake_resource_doc_version, fake_resource1):
    resource_id_to_data = {item["resource_id"]: item for item in fake_resource_doc_version.data}
    return G(
        ReleasedResourceDoc,
        gateway=fake_gateway,
        resource_version_id=fake_resource_version.id,
        resource_id=fake_resource1.id,
        language="zh",
        data=resource_id_to_data[fake_resource1.id],
    )


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
        GatewaySDK,
        gateway=fake_gateway,
        resource_version=fake_resource_version,
        language="python",
        is_recommended=True,
        is_public=True,
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
    def fn(method, view_name, path_params=None, gateway=None, user=None, app=None, **kwargs):
        path = reverse(view_name, kwargs=path_params)
        resolved = resolve(path)

        handler = getattr(request_factory, method.lower())
        request = handler(path=path, **kwargs)
        request.gateway = gateway
        if user is not None:
            request.user = user
        if app is not None:
            request.app = app

        response = resolved.func(request, *resolved.args, **resolved.kwargs)
        response.json = partial(get_response_json, response)

        return response

    return fn


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
def fake_plugin_type_bk_header_rewrite_schema():
    # apisix bk-header-rewrite plugin schema
    return G(
        Schema,
        name="bk_header_rewrite_schema",
        _schema=json.dumps(
            {
                "$comment": "this is a mark for our injected plugin schema",
                "type": "object",
                "description": "new headers for request",
                "minProperties": 1,
                "additionalProperties": False,
                "properties": {
                    "set": {
                        "type": "object",
                        "patternProperties": {"^[^:]+$": {"oneOf": [{"type": "string"}, {"type": "number"}]}},
                    },
                    "remove": {"type": "array", "items": {"type": "string", "pattern": "^[^:]+$"}},
                },
            }
        ),
    )


@pytest.fixture()
def fake_plugin_type_bk_header_rewrite(fake_gateway, fake_plugin_type_bk_header_rewrite_schema):
    return G(
        PluginType,
        code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value,
        name=PluginTypeCodeEnum.BK_HEADER_REWRITE.value,
        is_public=True,
        schema=fake_plugin_type_bk_header_rewrite_schema,
    )


@pytest.fixture
def fake_plugin_bk_header_rewrite(fake_plugin_type_bk_header_rewrite, fake_gateway, faker):
    return G(
        PluginConfig,
        gateway=fake_gateway,
        name="bk-header-rewrite",
        type=fake_plugin_type_bk_header_rewrite,
        yaml=yaml_dumps(
            {
                "set": [{"key": "foo", "value": "bar"}],
                "remove": [{"key": "baz"}],
            }
        ),
    )


@pytest.fixture()
def fake_plugin_stage_bk_header_rewrite_binding(fake_plugin_bk_header_rewrite, fake_stage):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_header_rewrite.gateway,
        config=fake_plugin_bk_header_rewrite,
        scope_type=PluginBindingScopeEnum.STAGE.value,
        scope_id=fake_stage.pk,
    )


@pytest.fixture()
def fake_plugin_resource_bk_header_rewrite_binding(fake_plugin_bk_header_rewrite, fake_resource):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_header_rewrite.gateway,
        config=fake_plugin_bk_header_rewrite,
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id=fake_resource.pk,
    )


@pytest.fixture()
def fake_plugin_type_bk_rate_limit(fake_gateway, fake_plugin_type_bk_header_rewrite_schema):
    return G(
        PluginType,
        code=PluginTypeCodeEnum.BK_RATE_LIMIT.value,
        name=PluginTypeCodeEnum.BK_RATE_LIMIT.value,
        is_public=True,
        schema=fake_plugin_type_bk_header_rewrite_schema,
    )


@pytest.fixture
def fake_plugin_bk_rate_limit(fake_plugin_type_bk_rate_limit, fake_gateway, faker):
    return G(
        PluginConfig,
        gateway=fake_gateway,
        name="bk-rate-limit",
        type=fake_plugin_type_bk_rate_limit,
        yaml=yaml_dumps(
            {
                "set": [{"key": "foo", "value": "bar"}],
                "remove": [{"key": "baz"}],
            }
        ),
    )


@pytest.fixture()
def fake_plugin_stage_bk_rate_limit_binding(fake_plugin_bk_rate_limit, fake_stage):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_rate_limit.gateway,
        config=fake_plugin_bk_rate_limit,
        scope_type=PluginBindingScopeEnum.STAGE.value,
        scope_id=fake_stage.pk,
    )


@pytest.fixture()
def fake_plugin_resource_bk_rate_limit_binding(fake_plugin_bk_rate_limit, fake_resource):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_rate_limit.gateway,
        config=fake_plugin_bk_rate_limit,
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id=fake_resource.pk,
    )


@pytest.fixture()
def fake_plugin_type_bk_cors(fake_plugin_type_bk_header_rewrite_schema):
    return G(
        PluginType,
        code=PluginTypeCodeEnum.BK_CORS.value,
        name=PluginTypeCodeEnum.BK_CORS.value,
        is_public=True,
        schema=fake_plugin_type_bk_header_rewrite_schema,  # 参数暂时用的是 bk-header-rewrite 的schema
    )


@pytest.fixture
def fake_plugin_bk_cors(fake_plugin_type_bk_cors, fake_gateway, faker):
    return G(
        PluginConfig,
        gateway=fake_gateway,
        name="bk-cors",
        type=fake_plugin_type_bk_cors,
        yaml=yaml_dumps(
            {
                "set": [{"key": "foo", "value": "bar"}],
                "remove": [{"key": "baz"}],
            }
        ),
    )


@pytest.fixture()
def fake_plugin_stage_bk_cors_binding(fake_plugin_bk_cors, fake_stage):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_cors.gateway,
        config=fake_plugin_bk_cors,
        scope_type=PluginBindingScopeEnum.STAGE.value,
        scope_id=fake_stage.pk,
    )


@pytest.fixture()
def fake_plugin_resource_bk_cors_binding(fake_plugin_bk_cors, fake_resource):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_cors.gateway,
        config=fake_plugin_bk_cors,
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id=fake_resource.pk,
    )


@pytest.fixture()
def fake_plugin_type_bk_ip_restriction(fake_plugin_type_bk_header_rewrite_schema):
    return G(
        PluginType,
        code=PluginTypeCodeEnum.BK_IP_RESTRICTION.value,
        name=PluginTypeCodeEnum.BK_IP_RESTRICTION.value,
        is_public=True,
        schema=fake_plugin_type_bk_header_rewrite_schema,  # 参数暂时用的是 bk-header-rewrite 的schema
    )


@pytest.fixture
def fake_plugin_bk_ip_restriction(fake_plugin_type_bk_ip_restriction, fake_gateway, faker):
    return G(
        PluginConfig,
        gateway=fake_gateway,
        name="bk-cors",
        type=fake_plugin_type_bk_ip_restriction,
        yaml=yaml_dumps(
            {
                "set": [{"key": "foo", "value": "bar"}],
                "remove": [{"key": "baz"}],
            }
        ),
    )


@pytest.fixture()
def fake_plugin_stage_bk_ip_restriction_binding(fake_plugin_bk_ip_restriction, fake_stage):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_ip_restriction.gateway,
        config=fake_plugin_bk_ip_restriction,
        scope_type=PluginBindingScopeEnum.STAGE.value,
        scope_id=fake_stage.pk,
    )


@pytest.fixture()
def fake_plugin_resource_bk_ip_restriction_binding(fake_plugin_bk_ip_restriction, fake_resource):
    return G(
        PluginBinding,
        gateway=fake_plugin_bk_ip_restriction.gateway,
        config=fake_plugin_bk_ip_restriction,
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id=fake_resource.pk,
    )


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
                "python_sdk_usage_example": "python_sdk_usage_example_v2.md",
            },
        },
    }

    return "open"


@pytest.fixture
def fake_resource_doc(faker, fake_resource):
    return G(
        ResourceDoc,
        gateway=fake_resource.gateway,
        resource_id=fake_resource.id,
        language=faker.random_element(
            ["en", "zh"],
        ),
    )


@pytest.fixture
def fake_resource_swagger():
    return json.dumps(
        {
            "swagger": "2.0",
            "basePath": "/",
            "info": {
                "version": "1.0.0",
                "title": "API Gateway Swagger",
            },
            "schemes": ["http"],
            "paths": {
                "/http/get/mapping/{userId}": {
                    "get": {
                        "operationId": "http_get_mapping_user_id",
                        "description": "test",
                        "tags": ["pet"],
                        "schemes": ["http"],
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "allowApplyPermission": True,
                            "matchSubpath": True,
                            "backend": {
                                "name": "default",
                                "path": "/hello/",
                                "method": "get",
                                "matchSubpath": True,
                                "timeout": 30,
                            },
                        },
                    },
                }
            },
        }
    )


@pytest.fixture
def fake_err_resource_swagger():
    return json.dumps(
        {
            "openapi": "3.0.3",
            "info": {
                "title": "custom-demo",
                "version": "1.0.0",
                "description": "这是应用 bk_apigateway 的 API 网关。由网关开发框架自动注册。",
            },
            "paths": {
                "/api/v1/demo/{id}/": {
                    "get": {
                        "operationId": "v1_demo_retrieve",
                        "description": "这是一个 demo api",
                        "parameters": [
                            {"in": "path", "name": "id", "schema": {"type": "integer"}, "required": True},
                            {
                                "in": "query",
                                "name": "name",
                                "schema": {"type": "string", "maxLength": 100, "minLength": 1},
                                "required": True,
                            },
                        ],
                        "tags": ["open"],
                        "security": [{"ApiGatewayJWTAuthentication": []}],
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/DemoRetrieveOutputSLZ"},
                                        "examples": {
                                            "Example": {
                                                "value": {"message": "hello, world, and my id is 1"},
                                                "summary": "example",
                                            }
                                        },
                                    }
                                },
                                "description": "",
                            }
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "matchSubpath": True,
                            "backend": {
                                "method": "get",
                                "path": "/api/v1/demo/{id}/",
                                "matchSubpath": True,
                                "timeout": 0,
                            },
                            "pluginConfigs": [
                                {
                                    "type": "bk-header-rewrite",
                                    "yaml": "remove:\n- X-Bar\nset:\n- key: X-Foo\n  value: test\n",
                                }
                            ],
                            "allowApplyPermission": True,
                            "authConfig": {
                                "userVerifiedRequired": True,
                                "appVerifiedRequired": True,
                                "resourcePermissionRequired": True,
                            },
                            "descriptionEn": "this is a demo api",
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "DemoRetrieveOutputSLZ": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    }
                },
                "securitySchemes": {
                    "ApiGatewayJWTAuthentication": {"type": "apiKey", "in": "header", "name": "X-BKAPI-JWT"}
                },
            },
        }
    )


@pytest.fixture
def fake_openapi_content():
    return {
        "swagger": "2.0",
        "basePath": "/",
        "info": {},
        "schemes": ["http"],
        "paths": {},
    }


@pytest.fixture
def fake_resource_dict():
    return {
        "method": "POST",
        "path": "/users",
        "match_subpath": False,
        "name": "add_user",
        "description": "创建新用户",
        "description_en": "Adds a new user",
        "labels": ["testing"],
        "is_public": True,
        "allow_apply_permission": True,
        "backend": {
            "name": "default",
            "config": {
                "method": "POST",
                "path": "/users",
                "match_subpath": False,
                "timeout": 0,
            },
        },
        "auth_config": {
            "auth_verified_required": True,
        },
    }


@pytest.fixture
def fake_resource_data(faker):
    return ResourceData(
        resource=None,
        name=faker.pystr(),
        description=faker.pystr(),
        method="GET",
        path=faker.pystr(),
        auth_config=ResourceAuthConfig(),
        backend_config=ResourceBackendConfig(method="GET", path=faker.pystr()),
    )
