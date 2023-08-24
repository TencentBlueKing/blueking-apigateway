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
import copy
import datetime
import json

import pytest
from ddf import G
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.resource import serializers
from apigateway.core import constants
from apigateway.core.models import Context, Gateway, Proxy, Resource, ResourceVersion, Stage, StageResourceDisabled
from apigateway.tests.utils.testing import create_request, dummy_time

pytestmark = pytest.mark.django_db


class TestQueryResourceSLZ:
    def test_to_internal_value(self):
        data = [
            {
                "query": "test",
                "path": "/echo/",
                "method": "POST",
                "label_name": "test",
                "expected": {
                    "query": "test",
                    "path": "/echo/",
                    "method": "POST",
                    "label_name": "test",
                },
            },
            {
                "query": "test",
                "expected": {
                    "query": "test",
                },
            },
            {
                "path": "/echo/",
                "method": "GET",
                "expected": {
                    "path": "/echo/",
                    "method": "GET",
                },
            },
        ]
        for test in data:
            slz = serializers.QueryResourceSLZ(data=test)
            slz.is_valid()
            assert slz.validated_data == test["expected"]


class TestListResourceSLZ:
    def test_to_representation(self):
        resource = G(
            Resource,
            name="test",
            description="desc",
            method="GET",
            path="/echo/",
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
        )
        resource_version = G(ResourceVersion, created_time=dummy_time.time + datetime.timedelta(seconds=10))

        data = [
            {
                "resource": resource,
                "resource_version": None,
                "resource_labels": {
                    resource.id: [
                        {
                            "id": 1,
                            "name": "test",
                        }
                    ]
                },
                "doc_languages_of_resources": {
                    resource.id: ["zh"],
                },
                "resource_released_stage_count": {
                    resource.id: 1,
                },
                "stage_count": 2,
                "expected": [
                    {
                        "id": resource.id,
                        "name": "test",
                        "description": "desc",
                        "description_en": None,
                        "method": "GET",
                        "path": "/echo/",
                        "updated_time": "2019-01-01 20:30:00",
                        "is_created": True,
                        "has_updated": True,
                        "released_stage_count": 1,
                        "unreleased_stage_count": 1,
                        "labels": [
                            {
                                "id": 1,
                                "name": "test",
                            }
                        ],
                        "resource_doc_languages": ["zh"],
                    }
                ],
            },
            {
                "resource": resource,
                "resource_version": resource_version,
                "resource_labels": {},
                "resource_released_stage_count": {
                    resource.id: 2,
                },
                "stage_count": 2,
                "doc_languages_of_resources": {},
                "expected": [
                    {
                        "id": resource.id,
                        "name": "test",
                        "description": "desc",
                        "description_en": None,
                        "method": "GET",
                        "path": "/echo/",
                        "updated_time": "2019-01-01 20:30:00",
                        "is_created": False,
                        "has_updated": False,
                        "released_stage_count": 2,
                        "unreleased_stage_count": 0,
                        "labels": [],
                        "resource_doc_languages": [],
                    }
                ],
            },
        ]

        for test in data:
            slz = serializers.ListResourceSLZ(
                [test["resource"]],
                many=True,
                context={
                    "resource_labels": test["resource_labels"],
                    "latest_resource_version": test["resource_version"],
                    "resource_released_stage_count": test["resource_released_stage_count"],
                    "stage_count": test["stage_count"],
                    "doc_languages_of_resources": test["doc_languages_of_resources"],
                },
            )
            assert slz.data == test["expected"]


class TestDefaultProxyHTTPConfigSLZ:
    def test_to_internal_value(self):
        data = [
            # ok
            {
                "method": "GET",
                "path": "/echo/",
                "timeout": 30,
                "upstreams": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                            "weight": 100,
                        }
                    ],
                },
                "transform_headers": {
                    "set": {"k1": "v1"},
                },
            },
            # ok, upstreams is empty
            {
                "method": "GET",
                "path": "/echo/",
                "timeout": 30,
                "upstreams": {},
                "transform_headers": {
                    "set": {"k1": "v1"},
                },
            },
            # host include stage var {env.domainv2}
            {
                "method": "GET",
                "path": "/echo/",
                "timeout": 30,
                "upstreams": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://{env.domainv2}",
                            "weight": 100,
                        }
                    ],
                },
                "transform_headers": {
                    "set": {"k1": "v1"},
                },
            },
            # transform_headers is empty, ok
            {
                "method": "GET",
                "path": "/echo/",
                "timeout": 30,
                "upstreams": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                            "weight": 100,
                        }
                    ],
                },
                "transform_headers": {},
            },
            # timeout, error
            {
                "method": "GET",
                "path": "/echo/",
                "timeout": -1,
                "upstreams": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                        }
                    ],
                },
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.DefaultProxyHTTPConfigSLZ(data=test)
            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors
            else:
                assert slz.validated_data == test


class TestResourceProxyMockConfigSLZ:
    def test_to_internal_value(self):
        data = [
            # ok
            {
                "code": 200,
                "body": "test",
                "headers": {"k1": "v1"},
            },
            # body is empty, ok
            {
                "code": 200,
                "body": "",
                "headers": {"k1": "v1"},
            },
            # headers is empty, ok
            {
                "code": 200,
                "body": "test",
                "headers": {},
            },
        ]
        for test in data:
            slz = serializers.ResourceProxyMockConfigSLZ(data=test)
            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors
            else:
                assert slz.validated_data == test


class TestAuthConfigSLZ:
    def test_to_internal_value(self):
        data = [
            # ok
            {
                "skip_auth_verification": True,
                "auth_verified_required": True,
                "app_verified_required": True,
                "resource_perm_required": True,
                "expected": {
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            },
            # skip_auth_verification not exist, ok
            {
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
                "expected": {
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            },
            {
                "auth_verified_required": False,
                "expected": {
                    "auth_verified_required": False,
                },
            },
            {
                "auth_verified_required": True,
                "expected": {
                    "auth_verified_required": True,
                },
            },
        ]
        for test in data:
            slz = serializers.AuthConfigSLZ(data=test)
            slz.is_valid()
            assert slz.validated_data == test["expected"]


class TestProxyConfigsSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            # ok
            (
                {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {},
                    },
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {},
                    },
                },
                {
                    "backend_config_type": "default",
                    "backend_service_id": None,
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {},
                    },
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {},
                    },
                },
            ),
            # http not exist, ok
            (
                {
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {},
                    },
                },
                {
                    "backend_config_type": "default",
                    "backend_service_id": None,
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {},
                    },
                },
            ),
            # mock not exist, ok
            (
                {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {},
                    },
                },
                {
                    "backend_config_type": "default",
                    "backend_service_id": None,
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {},
                    },
                },
            ),
            (
                {
                    "backend_config_type": "existed",
                    "backend_service_id": 1,
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        # "timeout": {"connect": 10, "read": 10, "send": 10},
                        "transform_headers": {},
                    },
                },
                {
                    "backend_config_type": "existed",
                    "backend_service_id": 1,
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        # "timeout": {"connect": 10, "read": 10, "send": 10},
                        "transform_headers": {},
                    },
                },
            ),
        ],
    )
    def test_validate(self, data, expected):
        slz = serializers.ProxyConfigsSLZ(data=data)
        assert slz.is_valid() is True
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "backend_config_type": "default",
                    "http": None,
                },
                {},
                None,
            ),
            (
                {
                    "backend_config_type": "default",
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": True,
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {"set": {"k1": "v1"}},
                    },
                },
                {
                    "method": "GET",
                    "path": "/echo/",
                    "match_subpath": True,
                    "timeout": 30,
                    "upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {
                                "host": "http://www.a.com",
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {"set": {"k1": "v1"}},
                },
                None,
            ),
            (
                {
                    "backend_config_type": "existed",
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": True,
                        # "timeout": {"connect": 10, "send": 10, "read": 10},
                        "transform_headers": {"set": {"k1": "v1"}},
                    },
                },
                {
                    "method": "GET",
                    "path": "/echo/",
                    "match_subpath": True,
                    # "timeout": {"connect": 10, "send": 10, "read": 10},
                    "transform_headers": {"set": {"k1": "v1"}},
                },
                None,
            ),
        ],
    )
    def test_validate_http(self, data, expected, expected_error):
        slz = serializers.ProxyConfigsSLZ(data=data)

        if expected_error:
            with pytest.raises(expected_error):
                slz._validate_http(**data)
            return

        assert slz._validate_http(**data) == expected

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "backend_config_type": "default",
                    "backend_service_id": None,
                },
                None,
                None,
            ),
            (
                {
                    "backend_config_type": "default",
                    "backend_service_id": 1,
                },
                None,
                None,
            ),
            (
                {
                    "backend_config_type": "existed",
                    "backend_service_id": 1,
                },
                1,
                None,
            ),
            (
                {
                    "backend_config_type": "existed",
                    "backend_service_id": None,
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_backend_service_id(self, data, expected, expected_error):
        slz = serializers.ProxyConfigsSLZ(data=data)

        if expected_error:
            with pytest.raises(expected_error):
                slz._validate_backend_service_id(**data)
            return

        assert slz._validate_backend_service_id(**data) == expected


class TestResourceSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_valid",
        [
            (
                {
                    "name": "post_echo",
                    "description": "",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 30,
                            "upstreams": {
                                "loadbalance": "roundrobin",
                                "hosts": [
                                    {
                                        "host": "http://www.a.com",
                                        "weight": 100,
                                    }
                                ],
                            },
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                },
                {
                    "name": "post_echo",
                    "description": "",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "backend_config_type": "default",
                        "backend_service_id": None,
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 30,
                            "upstreams": {
                                "loadbalance": "roundrobin",
                                "hosts": [
                                    {
                                        "host": "http://www.a.com",
                                        "weight": 100,
                                    }
                                ],
                            },
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                },
                True,
            ),
            # ok, proxy_configs timeout/upstreams/transform_headers is null
            (
                {
                    "name": "post_echo_2",
                    "description": "",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                {
                    "name": "post_echo_2",
                    "description": "",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "backend_config_type": "default",
                        "backend_service_id": None,
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                True,
            ),
            (
                # error, proxy_configs.http is empty
                {
                    "name": "post_echo_3",
                    "description": "",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {},
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                None,
                False,
            ),
        ],
    )
    def test_validate(self, fake_gateway, data, expected, expected_valid):
        slz = serializers.ResourceSLZ(data=data, context={"api": fake_gateway})

        assert slz.is_valid() is expected_valid

        if not expected_valid:
            return

        expected["api"] = fake_gateway
        assert slz.validated_data == expected

    def test_to_representation(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        stage_prod = G(Stage, gateway=gateway, name="prod")
        label = G(APILabel, api=gateway, name="label")

        G(
            Context,
            scope_type=constants.ContextScopeTypeEnum.RESOURCE.value,
            scope_id=resource.id,
            type=constants.ContextTypeEnum.RESOURCE_AUTH.value,
            _config=json.dumps(
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                }
            ),
        )

        proxy_http = G(
            Proxy,
            resource=resource,
            type="http",
            _config=json.dumps(
                {
                    "method": "GET",
                    "path": "/echo/",
                    "match_subpath": False,
                    "timeout": 30,
                    "upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {
                                "host": "http://www.a.com",
                            }
                        ],
                    },
                    "transform_headers": {},
                }
            ),
        )
        G(
            Proxy,
            resource=resource,
            type="mock",
            _config=json.dumps(
                {
                    "code": 200,
                    "body": "test",
                    "headers": {},
                }
            ),
        )
        resource.proxy_id = proxy_http.id
        resource.save()

        G(ResourceLabel, resource=resource, api_label=label)
        G(StageResourceDisabled, resource=resource, stage=stage_prod)

        slz = serializers.ResourceSLZ(instance=resource)

        assert slz.data == {
            "id": resource.id,
            "name": resource.name,
            "description": resource.description,
            "description_en": resource.description_en,
            "is_public": resource.is_public,
            "allow_apply_permission": resource.allow_apply_permission,
            "label_ids": [label.id],
            "method": resource.method,
            "path": resource.path,
            "match_subpath": resource.match_subpath,
            "proxy_type": "http",
            "proxy_configs": {
                "backend_config_type": "default",
                "backend_service_id": None,
                "http": {
                    "method": "GET",
                    "path": "/echo/",
                    "match_subpath": False,
                    "timeout": 30,
                    "upstreams": {"loadbalance": "roundrobin", "hosts": [{"host": "http://www.a.com"}]},
                    "transform_headers": {},
                },
                "mock": {"code": 200, "body": "test", "headers": {}},
            },
            "auth_config": {
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            "disabled_stage_ids": [stage_prod.id],
        }

    def test_validate_method(self):
        gateway = G(Gateway)
        G(Resource, api=gateway, path="/echo/any-exists/", method="ANY")
        G(Resource, api=gateway, path="/echo/get-exists/", method="GET")

        data = [
            {
                "path": "/echo/any-exists/",
                "method": "GET",
                "will_error": True,
            },
            {
                "path": "/echo/get-exists/",
                "method": "ANY",
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.ResourceSLZ(data=test)

            if test.get("will_error"):
                with pytest.raises(Exception):
                    slz._validate_method(gateway, test["path"], test["method"])
                return

            slz._validate_method(gateway, test["path"], test["method"])


class TestCheckProxyPathSLZ:
    def test_validate(self):
        gateway = G(Gateway)
        G(
            Stage,
            gateway=gateway,
            name="prod",
            _vars=json.dumps(
                {
                    "region": "sz",
                }
            ),
        )

        request = create_request()
        request.gateway = gateway

        data = [
            # ok
            {
                "path": "/echo/",
                "proxy_path": "/echo/",
            },
            # ok, has path-vars
            {
                "path": "/echo/{username}/",
                "proxy_path": "/echo/{username}/",
            },
            # ok, has stage vars
            {
                "path": "/echo/{username}/",
                "proxy_path": "/echo/{username}/{env.region}/",
            },
            # error, proxy_path has query-string
            {
                "path": "/echo/",
                "proxy_path": "/echo/?a=b&c=d",
                "will_error": True,
            },
            # error, stage vars not exist
            {
                "path": "/echo/{username}/",
                "proxy_path": "/echo/{username}/{env.project}/",
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.CheckProxyPathSLZ(data=test, context={"request": request})
            slz.is_valid()

            if test.get("will_error"):
                assert slz.errors
            else:
                assert not slz.errors


class TestResourceImportSLZ:
    @pytest.mark.parametrize(
        "selected_resources, expected, will_error",
        [
            (None, None, False),
            ([{"name": "get_user"}], [{"name": "get_user"}], False),
            ([], None, True),
        ],
    )
    def test_selected_resources(self, mocker, faker, selected_resources, expected, will_error):
        slz = serializers.ResourceImportSLZ(
            data={
                "content": faker.pystr(),
                "selected_resources": selected_resources,
            }
        )

        if will_error:
            with pytest.raises(drf_serializers.ValidationError):
                slz.is_valid(raise_exception=True)
            return

        slz.is_valid(raise_exception=True)
        assert slz.validated_data["selected_resources"] == expected


class TestCheckImportResourceSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway
        self.context = {
            "request": self.request,
            "stage_name_set": set(["prod", "test"]),
            "resource_path_method_to_id": {
                "/echo/": {
                    "GET": 1,
                    "POST": 2,
                },
                "/echo/any/": {
                    "ANY": 3,
                },
            },
            "resource_name_to_id": {
                "get_echo": 1,
                "post_echo": 2,
                "any_echo": 3,
            },
            "resource_doc_language": "zh",
            "resource_doc_key_to_id": {
                "1:zh": 10,
                "2:zh": 20,
            },
        }

    def test_to_internal_value(self):
        data = [
            {
                "resource": {
                    "id": None,
                    "name": "echo_2",
                    "path": "/echo/2/",
                    "method": "GET",
                    "labels": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": True,
                    },
                    "disabled_stages": ["prod"],
                },
                "expected": {
                    "id": None,
                    "name": "echo_2",
                    "path": "/echo/2/",
                    "method": "GET",
                    "labels": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "backend_config_type": "default",
                        "backend_service_id": None,
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": True,
                    },
                    "disabled_stages": ["prod"],
                    "resource_doc_id": None,
                    "resource_doc_language": "zh",
                },
            },
            {
                "resource": {
                    "id": 1,
                    "name": "get_echo",
                    "path": "/echo/",
                    "method": "GET",
                    "labels": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": True,
                    },
                    "disabled_stages": ["prod"],
                },
                "expected": {
                    "id": 1,
                    "name": "get_echo",
                    "path": "/echo/",
                    "method": "GET",
                    "labels": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "backend_config_type": "default",
                        "backend_service_id": None,
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": True,
                    },
                    "disabled_stages": ["prod"],
                    "resource_doc_id": 10,
                    "resource_doc_language": "zh",
                },
            },
        ]
        for test in data:
            slz = serializers.CheckImportResourceSLZ(
                data=test["resource"],
                context=copy.deepcopy(self.context),
            )
            slz.is_valid(raise_exception=True)
            assert dict(slz.validated_data) == test["expected"]

    def test_validate_labels(self):
        data = [
            {
                "resource": {
                    "name": "get_echo",
                    "path": "/echo/",
                    "method": "GET",
                    "labels": ["a"] * 11,
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": True,
                    },
                    "disabled_stages": ["prod"],
                },
            }
        ]
        for test in data:
            slz = serializers.CheckImportResourceSLZ(
                data=test["resource"],
                context=copy.deepcopy(self.context),
            )
            slz.is_valid()
            assert slz.errors

    def test_validate_disabled_stages(self):
        data = [
            {
                "resource": {
                    "name": "disabled_stages",
                    "path": "/disabled/stages/",
                    "method": "GET",
                    "labels": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        },
                    },
                    "auth_config": {
                        "auth_verified_required": True,
                    },
                    "disabled_stages": ["prod", "stag"],
                },
                "expected": {
                    "disabled_stages": ["prod"],
                },
            }
        ]
        for test in data:
            slz = serializers.CheckImportResourceSLZ(
                data=test["resource"],
                context=copy.deepcopy(self.context),
            )
            slz.is_valid(raise_exception=True)
            assert slz.validated_data["disabled_stages"] == test["expected"]["disabled_stages"]

    def test_validate_method(self):
        resource = {
            "labels": [],
            "proxy_type": "http",
            "proxy_configs": {
                "http": {
                    "method": "GET",
                    "path": "/echo/",
                    "timeout": 0,
                    "upstreams": {},
                    "transform_headers": {},
                },
            },
            "auth_config": {
                "auth_verified_required": True,
            },
            "disabled_stages": [],
        }

        data = [
            # same path, other method exist
            {
                "resource": [
                    {
                        "name": "any_echo_1",
                        "path": "/echo/",
                        "method": "ANY",
                    },
                ],
                "will_error": True,
            },
            # same path, any method exist
            {
                "resource": [
                    {
                        "name": "any_echo_2",
                        "path": "/echo/any/",
                        "method": "GET",
                    }
                ],
                "will_error": True,
            },
            # same path, same method exist in config
            {
                "resource": [
                    {
                        "name": "echo_2",
                        "path": "/echo/2/",
                        "method": "GET",
                    },
                    {
                        "name": "echo_3",
                        "path": "/echo/2/",
                        "method": "GET",
                    },
                ],
                "will_error": True,
            },
            # same path, any method exist
            {
                "resource": [
                    {
                        "name": "echo_2",
                        "path": "/echo/2/",
                        "method": "ANY",
                    },
                    {
                        "name": "echo_3",
                        "path": "/echo/2/",
                        "method": "GET",
                    },
                ],
                "will_error": True,
            },
            # same path, any method, other method exist
            {
                "resource": [
                    {
                        "name": "echo_2",
                        "path": "/echo/2/",
                        "method": "GET",
                    },
                    {
                        "name": "echo_3",
                        "path": "/echo/2/",
                        "method": "ANY",
                    },
                ],
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.CheckImportResourceSLZ(
                data=test["resource"],
                context=copy.deepcopy(self.context),
                many=True,
            )
            for r in test["resource"]:
                r.update(resource)

            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors
            else:
                assert not slz.errors
