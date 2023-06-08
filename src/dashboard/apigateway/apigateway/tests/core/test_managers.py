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
import datetime
import json

import pytest
from django.conf import settings
from django.test import TestCase
from django.utils.encoding import smart_bytes
from django_dynamic_fixture import G

from apigateway.biz.stage import StageHandler
from apigateway.common.error_codes import APIError
from apigateway.common.exceptions import InstanceDeleteError
from apigateway.common.mcryptography import AESCipherManager
from apigateway.core import constants
from apigateway.core.constants import (
    APIHostingTypeEnum,
    APIStatusEnum,
    SSLCertificateBindingScopeTypeEnum,
    StageStatusEnum,
)
from apigateway.core.models import (
    JWT,
    APIRelatedApp,
    BackendService,
    Gateway,
    MicroGateway,
    Proxy,
    Release,
    ReleasedResource,
    ReleaseHistory,
    Resource,
    ResourceVersion,
    SslCertificate,
    SslCertificateBinding,
    Stage,
    StageItem,
    StageItemConfig,
    StageResourceDisabled,
)
from apigateway.tests.utils.testing import create_gateway, dummy_time

pytestmark = pytest.mark.django_db


class TestGatewayManager:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway, created_by="admin")

    def test_search_apis(self):
        gateway = create_gateway(name="search-apis-test-a")
        gateway_2 = create_gateway(name="search-apis-test-b")

        stage_prod = G(Stage, api=gateway, name="prod")
        stage_test = G(Stage, api=gateway, name="test")

        G(Resource, api=gateway)
        resource_version = G(ResourceVersion, api=gateway)
        G(Release, api=gateway, stage=stage_prod, resource_version=resource_version)

        gateway.resource_count = 1
        gateway.stages = [
            {
                "stage_id": stage_prod.id,
                "stage_name": "prod",
                "stage_release_status": True,
            },
            {
                "stage_id": stage_test.id,
                "stage_name": "test",
                "stage_release_status": False,
            },
        ]
        gateway_2.resource_count = 0
        gateway_2.stages = []

        data = [
            {
                "username": "admin",
                "name": "search-apis-test",
                "expected": [gateway, gateway_2],
            }
        ]
        for test in data:
            result = Gateway.objects.search_gateways(test["username"], test["name"])
            assert result[0] == test["expected"][0]
            assert result[1] == test["expected"][1]

    def test_query_micro_and_active_ids(self):
        g1 = G(Gateway, hosting_type=APIHostingTypeEnum.DEFAULT.value, status=APIStatusEnum.ACTIVE.value)
        g2 = G(Gateway, hosting_type=APIHostingTypeEnum.DEFAULT.value, status=APIStatusEnum.INACTIVE.value)
        g3 = G(Gateway, hosting_type=APIHostingTypeEnum.MICRO.value, status=APIStatusEnum.ACTIVE.value)
        g4 = G(Gateway, hosting_type=APIHostingTypeEnum.MICRO.value, status=APIStatusEnum.INACTIVE.value)

        result = Gateway.objects.query_micro_and_active_ids()
        assert g3.id in result
        assert g1.id not in result
        assert g2.id not in result
        assert g4.id not in result

        result = Gateway.objects.query_micro_and_active_ids(ids=[g4.id])
        assert g3.id not in result


class TestStageManager:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    def test_get_stage_ids(self):
        gateway = G(Gateway)
        s1 = G(Stage, api=gateway)
        s2 = G(Stage, api=gateway)

        result = Stage.objects.get_ids(gateway.id)
        assert sorted(result) == [s1.id, s2.id]

    def test_get_id_to_fields(self, fake_gateway):
        result = Stage.objects.get_id_to_fields(gateway_id=fake_gateway.id, fields=["id", "name"])
        assert result == {}

        s1 = G(Stage, api=fake_gateway)
        s2 = G(Stage, api=fake_gateway)

        result = Stage.objects.get_id_to_fields(gateway_id=fake_gateway.id, fields=["id", "name"])
        assert result == {
            s1.id: {"id": s1.id, "name": s1.name},
            s2.id: {"id": s2.id, "name": s2.name},
        }

    def test_get_name_id_map(self):
        gateway = G(Gateway)
        s1 = G(Stage, api=gateway, name="prod")
        s2 = G(Stage, api=gateway, name="test")

        result = Stage.objects.get_name_id_map(gateway)
        assert result == {"prod": s1.id, "test": s2.id}

    def test_create_stage(self):
        gateway = G(Gateway)
        data = [
            {
                "api": gateway,
                "created_by": "admin",
            }
        ]
        for test in data:
            result = StageHandler().create_default(
                test["api"],
                created_by=test["created_by"],
            )
            assert result.api == test["api"]
            assert result.name == "prod"
            assert result.vars == {}
            assert result.status == constants.StageStatusEnum.INACTIVE.value
            assert result.created_by == test["created_by"]

    def test_get_micro_gateway_id_to_fields(self):
        gateway = G(Gateway)

        micro_gateway = G(MicroGateway, api=gateway)

        G(Stage, api=gateway)
        s2 = G(Stage, api=gateway, micro_gateway=micro_gateway)

        result = Stage.objects.get_micro_gateway_id_to_fields(gateway.id)
        assert result == {
            micro_gateway.id: {
                "id": s2.id,
                "name": s2.name,
                "micro_gateway_id": micro_gateway.id,
            }
        }

    def test_get_gateway_name_to_active_stage_names(self):
        gateway = G(Gateway)

        s1 = G(Stage, api=gateway, name="s1", status=StageStatusEnum.ACTIVE.value)
        s2 = G(Stage, api=gateway, name="s2", status=StageStatusEnum.INACTIVE.value)
        s3 = G(Stage, api=gateway, name="s3", status=StageStatusEnum.ACTIVE.value)

        result = Stage.objects.get_gateway_name_to_active_stage_names([gateway])
        assert result == {gateway.name: ["s1", "s3"]}


class TestResourceManager:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    def test_get_api_resource_count(self):
        gateway_1 = G(Gateway)
        gateway_2 = G(Gateway)
        gateway_3 = G(Gateway)

        G(Resource, api=gateway_1)
        G(Resource, api=gateway_1)
        G(Resource, api=gateway_2)

        data = [
            {
                "gateway_ids": [gateway_1.id, gateway_2.id, gateway_3.id],
                "expected": {
                    gateway_1.id: 2,
                    gateway_2.id: 1,
                },
            },
            {
                "gateway_ids": [gateway_1.id, gateway_2.id],
                "expected": {
                    gateway_1.id: 2,
                    gateway_2.id: 1,
                },
            },
        ]

        for test in data:
            result = Resource.objects.get_api_resource_count(test["gateway_ids"])
            assert result == test["expected"]

    def test_filter_valid_ids(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)

        data = [
            {
                "ids": [],
                "expected": [],
            },
            {
                "ids": [0],
                "expected": [],
            },
            {
                "ids": [resource.id + 1],
                "expected": [],
            },
            {
                "ids": [resource.id],
                "expected": [resource.id],
            },
        ]
        for test in data:
            result = Resource.objects.filter_valid_ids(gateway, test["ids"])
            assert result == test["expected"]

    def test_filter_resource_path_method_to_id(self):
        r1 = G(Resource, api=self.gateway, path="/hello/", method="GET")
        r2 = G(Resource, api=self.gateway, path="/hello/", method="POST")
        r3 = G(Resource, api=self.gateway, path="/hello/{user_id}/", method="POST")
        r4 = G(Resource, api=self.gateway, path="/test/", method="ANY")

        expected = {
            "/hello/": {
                "GET": r1.id,
                "POST": r2.id,
            },
            "/hello/{user_id}/": {
                "POST": r3.id,
            },
            "/test/": {
                "ANY": r4.id,
            },
        }
        result = Resource.objects.filter_resource_path_method_to_id(self.gateway.id)
        assert result == expected

    def test_filter_id_to_fields(self):
        gateway = G(Gateway)

        r1 = G(Resource, api=gateway, method="GET", path="/echo/", name="get_echo")
        r2 = G(Resource, api=gateway, method="POST", path="/echo/", name="post_echo")

        result = Resource.objects.filter_id_to_fields(gateway.id, ["id", "name", "method", "path"])
        assert result == {
            r1.id: {
                "id": r1.id,
                "name": "get_echo",
                "method": "GET",
                "path": "/echo/",
            },
            r2.id: {
                "id": r2.id,
                "name": "post_echo",
                "method": "POST",
                "path": "/echo/",
            },
        }

    def test_filter_id_is_public_map(self):
        gateway = G(Gateway)

        r1 = G(Resource, api=gateway, is_public=True)
        r2 = G(Resource, api=gateway, is_public=False)

        result = Resource.objects.filter_id_is_public_map(gateway.id)
        assert result == {r1.id: True, r2.id: False}

    def test_group_by_api_id(self):
        a1 = G(Gateway)
        a2 = G(Gateway)

        r1 = G(Resource, api=a1)
        r2 = G(Resource, api=a2)
        r3 = G(Resource, api=a1)

        result = Resource.objects.group_by_api_id([r1.id, r2.id, r3.id])
        assert result == {
            a1.id: [r1.id, r3.id],
            a2.id: [r2.id],
        }

    def test_get_id_to_name(self):
        gateway = G(Gateway)

        r = G(Resource, api=gateway, name="test")

        assert Resource.objects.get_id_to_name(gateway.id) == {r.id: "test"}
        assert Resource.objects.get_id_to_name(gateway.id, [r.id]) == {r.id: "test"}
        assert Resource.objects.get_id_to_name(gateway.id, []) == {}

    def test_get_unspecified_resource_fields(self):
        gateway = G(Gateway)

        r1 = G(Resource, api=gateway, name="r1", method="GET", path="/echo/r1/")
        r2 = G(Resource, api=gateway, name="r2", method="POST", path="/echo/r2/")
        r3 = G(Resource, api=gateway, name="r3", method="POST", path="/echo/r3/")

        assert Resource.objects.get_unspecified_resource_fields(gateway.id, []) == [
            {"id": r1.id, "name": "r1", "method": "GET", "path": "/echo/r1/"},
            {"id": r2.id, "name": "r2", "method": "POST", "path": "/echo/r2/"},
            {"id": r3.id, "name": "r3", "method": "POST", "path": "/echo/r3/"},
        ]

        assert Resource.objects.get_unspecified_resource_fields(gateway.id, [r2.id]) == [
            {"id": r1.id, "name": "r1", "method": "GET", "path": "/echo/r1/"},
            {"id": r3.id, "name": "r3", "method": "POST", "path": "/echo/r3/"},
        ]

    def test_get_resource_ids_by_names(self):
        gateway = G(Gateway)
        resource_1 = G(Resource, name="red", api=gateway)
        resource_2 = G(Resource, name="green", api=gateway)

        assert Resource.objects.get_resource_ids_by_names(gateway.id, None) == []
        assert Resource.objects.get_resource_ids_by_names(gateway.id, []) == []
        assert Resource.objects.get_resource_ids_by_names(gateway.id, ["red"]) == [resource_1.id]
        assert Resource.objects.get_resource_ids_by_names(gateway.id, ["red", "green"]) == [
            resource_1.id,
            resource_2.id,
        ]


class TestContextManager(TestCase):
    pass


class TestProxyManager(TestCase):
    def test_save_proxy_config(self):
        resource = G(Resource)

        data = [
            {
                "type": "http",
                "configs": {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 10,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "replace": {"k1": "v1", "k2": "v2"},
                        },
                    }
                },
            },
            {
                "type": "mock",
                "configs": {
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {
                            "k1": "v1",
                        },
                    }
                },
            },
            {
                "type": "mock",
                "configs": {
                    "mock": {
                        "code": "invalid",
                    }
                },
                "will_error": True,
            },
        ]

        for test in data:
            if not test.get("will_error"):
                Proxy.objects.save_proxy_config(resource, test["type"], test["configs"][test["type"]])
                self.assertEqual(Proxy.objects.filter(resource=resource, type=test["type"]).count(), 1)
                continue

            with self.assertRaises(Exception):
                Proxy.objects.save_proxy_config(resource, test["type"], test["configs"][test["type"]])

    def test_get_proxy_type(self):
        resource = G(Resource)
        proxy = G(Proxy, resource=resource, type="http")

        result = Proxy.objects.get_proxy_type(proxy.id)
        self.assertEqual(result, "http")

    def test_filter_proxies(self):
        resource = G(Resource)
        proxy, _ = Proxy.objects.save_proxy_config(
            resource,
            "http",
            {
                "method": "GET",
                "path": "/echo/",
                "timeout": 10,
                "upstreams": {},
                "transform_headers": {},
            },
        )
        result = Proxy.objects.filter_proxies([resource.id])

        self.assertEqual(
            result,
            {
                proxy.id: {
                    "type": "http",
                    "config": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 10,
                        "upstreams": {},
                        "transform_headers": {},
                    },
                }
            },
        )


class TestResourceVersionManager:
    def test_get_used_stage_vars(self):
        gateway = G(Gateway)

        data = [
            # resource version not exist
            {
                "resource_version": None,
                "expected": None,
            },
            # proxy type is mock
            {
                "resource_version": G(
                    ResourceVersion,
                    api=gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "mock",
                                }
                            }
                        ]
                    ),
                ),
                "expected": {
                    "in_path": [],
                    "in_host": [],
                },
            },
            # vars in path/host
            {
                "resource_version": G(
                    ResourceVersion,
                    api=gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "http",
                                    "config": json.dumps(
                                        {
                                            "path": "/hello/{env.region}/",
                                            "upstreams": {
                                                "hosts": [
                                                    {"host": "https://{env.domain}"},
                                                ]
                                            },
                                        }
                                    ),
                                }
                            }
                        ]
                    ),
                ),
                "expected": {
                    "in_path": ["region"],
                    "in_host": ["domain"],
                },
            },
            # vars in path/host
            {
                "resource_version": G(
                    ResourceVersion,
                    api=gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "http",
                                    "config": json.dumps(
                                        {
                                            "path": "/hello/{env.region}/",
                                            "upstreams": {},
                                        }
                                    ),
                                }
                            }
                        ]
                    ),
                ),
                "expected": {
                    "in_path": ["region"],
                    "in_host": [],
                },
            },
        ]
        for test in data:
            result = ResourceVersion.objects.get_used_stage_vars(
                gateway_id=gateway.id,
                id=test["resource_version"].id if test["resource_version"] else 0,
            )
            assert result == test["expected"]

    def test_get_id_to_fields_map(self):
        gateway = G(Gateway)
        rv1 = G(ResourceVersion, api=gateway, name="rv1", title="rv1", version="1.0.1")
        rv2 = G(ResourceVersion, api=gateway, name="rv2", title="rv2", version="1.0.2")

        data = [
            {
                "params": {
                    "gateway_id": gateway.id,
                    "resource_version_ids": None,
                },
                "expected": {
                    rv1.id: {"id": rv1.id, "name": rv1.name, "title": rv1.title, "version": "1.0.1"},
                    rv2.id: {"id": rv2.id, "name": rv2.name, "title": rv2.title, "version": "1.0.2"},
                },
            },
            {
                "params": {
                    "gateway_id": gateway.id,
                    "resource_version_ids": [rv1.id],
                },
                "expected": {
                    rv1.id: {"id": rv1.id, "name": rv1.name, "title": rv1.title, "version": "1.0.1"},
                },
            },
        ]
        for test in data:
            result = ResourceVersion.objects.get_id_to_fields_map(**test["params"])
            assert result == test["expected"]

    def test_get_id_by_name(self, unique_id):
        gateway = G(Gateway)

        result = ResourceVersion.objects.get_id_by_name(gateway, unique_id)
        assert result is None

        resource_version = G(ResourceVersion, api=gateway, name=unique_id)
        result = ResourceVersion.objects.get_id_by_name(gateway, unique_id)
        assert result == resource_version.id

    def test_get_id_by_version(self, unique_id):
        gateway = G(Gateway)

        result = ResourceVersion.objects.get_id_by_version(gateway, unique_id)
        assert result is None

        resource_version = G(ResourceVersion, api=gateway, version=unique_id)
        result = ResourceVersion.objects.get_id_by_version(gateway, unique_id)
        assert result == resource_version.id

    def test_has_used_stage_upstreams(self, fake_gateway):
        data = [
            # proxy type is mock
            {
                "resource_version": G(
                    ResourceVersion,
                    api=fake_gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "mock",
                                }
                            }
                        ]
                    ),
                ),
                "expected": False,
            },
            # custom upstreams
            {
                "resource_version": G(
                    ResourceVersion,
                    api=fake_gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "http",
                                    "config": json.dumps(
                                        {
                                            "path": "/echo/",
                                            "upstreams": {
                                                "hosts": [
                                                    {"host": "http://example.com"},
                                                ]
                                            },
                                        }
                                    ),
                                }
                            }
                        ]
                    ),
                ),
                "expected": False,
            },
            # use stage upstreams
            {
                "resource_version": G(
                    ResourceVersion,
                    api=fake_gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "http",
                                    "config": json.dumps(
                                        {
                                            "path": "/echo/",
                                            "upstreams": {},
                                        }
                                    ),
                                }
                            }
                        ]
                    ),
                ),
                "expected": True,
            },
        ]
        for test in data:
            result = ResourceVersion.objects.has_used_stage_upstreams(
                gateway_id=fake_gateway.id,
                id=test["resource_version"].id,
            )
            assert result == test["expected"]

    def test_get_object_fields(self, fake_resource_version):
        expected = {
            "id": fake_resource_version.id,
            "name": fake_resource_version.name,
            "title": fake_resource_version.title,
            "version": fake_resource_version.version,
        }

        assert ResourceVersion.objects.get_object_fields(fake_resource_version.id) == expected

        fake_resource_version.delete()
        assert ResourceVersion.objects.get_object_fields(expected["id"]) == {}

    def test_filter_objects_fields(self, fake_resource_version):
        expected = [
            {
                "id": fake_resource_version.id,
                "version": fake_resource_version.version,
                "title": fake_resource_version.title,
                "comment": fake_resource_version.comment,
            }
        ]
        assert (
            list(
                ResourceVersion.objects.filter_objects_fields(
                    fake_resource_version.api.id,
                    version=fake_resource_version.version,
                )
            )
            == expected
        )


class TestStageResourceDisabledManager(TestCase):
    def test_get_disabled_stages(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        stage_prod = G(Stage, api=gateway, name="prod")
        stage_test = G(Stage, api=gateway, name="test")

        G(StageResourceDisabled, resource=resource, stage=stage_prod)
        G(StageResourceDisabled, resource=resource, stage=stage_test)

        result = StageResourceDisabled.objects.get_disabled_stages(resource.id)
        self.assertEqual(
            result,
            [
                {
                    "id": stage_prod.id,
                    "name": stage_prod.name,
                },
                {
                    "id": stage_test.id,
                    "name": stage_test.name,
                },
            ],
        )

    def test_filter_disabled_stages_by_gateway(self):
        gateway = G(Gateway)
        resource1 = G(Resource, api=gateway)
        resource2 = G(Resource, api=gateway)
        stage_prod = G(Stage, api=gateway, name="prod")
        stage_test = G(Stage, api=gateway, name="test")

        G(StageResourceDisabled, resource=resource1, stage=stage_prod)
        G(StageResourceDisabled, resource=resource2, stage=stage_prod)
        G(StageResourceDisabled, resource=resource1, stage=stage_test)

        result = StageResourceDisabled.objects.filter_disabled_stages_by_gateway(gateway)
        self.assertEqual(
            result,
            {
                resource1.id: [
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                    },
                    {
                        "id": stage_test.id,
                        "name": stage_test.name,
                    },
                ],
                resource2.id: [
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                    },
                ],
            },
        )


class TestReleaseManager:
    def test_get_stage_release_status(self):
        gateway = G(Gateway)

        stage_prod = G(Stage, api=gateway, name="prod", status=1)
        stage_test = G(Stage, api=gateway, name="test", status=1)

        resource_version = G(ResourceVersion, api=gateway)
        G(Release, api=gateway, stage=stage_prod, resource_version=resource_version)

        data = [
            {
                "stage_ids": [stage_prod.id, stage_test.id],
                "expected": {
                    stage_prod.id: True,
                },
            }
        ]
        for test in data:
            result = Release.objects.get_stage_release_status(test["stage_ids"])
            assert result == test["expected"]

    def test_get_stage_release(self):
        gateway = G(Gateway)

        stage_prod = G(Stage, api=gateway, name="prod", status=1)
        stage_test = G(Stage, api=gateway, name="test", status=1)

        resource_version = G(ResourceVersion, api=gateway, name="test-01", title="test", version="1.0.1")
        G(Release, api=gateway, stage=stage_prod, resource_version=resource_version, updated_time=dummy_time.time)

        data = [
            {
                "stage_ids": [stage_prod.id, stage_test.id],
                "expected": {
                    stage_prod.id: {
                        "release_status": True,
                        "release_time": dummy_time.time,
                        "resource_version_id": resource_version.id,
                        "resource_version_name": "test-01",
                        "resource_version_title": "test",
                        "resource_version_display": "1.0.1(test)",
                        "resource_version": {
                            "version": "1.0.1",
                        },
                    },
                },
            }
        ]
        for test in data:
            result = Release.objects.get_stage_release(gateway, test["stage_ids"])
            assert result == test["expected"]

    def test_get_released_stages(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, api=gateway, name="prod", status=1)
        stage_test = G(Stage, api=gateway, name="test", status=1)
        stage_dev = G(Stage, api=gateway, name="dev", status=1)
        resource_version_1 = G(ResourceVersion, api=gateway)
        resource_version_2 = G(ResourceVersion, api=gateway)
        G(Release, api=gateway, stage=stage_prod, resource_version=resource_version_1)
        G(Release, api=gateway, stage=stage_dev, resource_version=resource_version_2)
        G(Release, api=gateway, stage=stage_test, resource_version=resource_version_1)

        data = [
            {
                "resource_version_ids": None,
                "expected": {
                    resource_version_2.id: [
                        {
                            "id": stage_dev.id,
                            "name": stage_dev.name,
                        },
                    ],
                    resource_version_1.id: [
                        {
                            "id": stage_prod.id,
                            "name": stage_prod.name,
                        },
                        {
                            "id": stage_test.id,
                            "name": stage_test.name,
                        },
                    ],
                },
            },
            {
                "resource_version_ids": [resource_version_1.id],
                "expected": {
                    resource_version_1.id: [
                        {
                            "id": stage_prod.id,
                            "name": stage_prod.name,
                        },
                        {
                            "id": stage_test.id,
                            "name": stage_test.name,
                        },
                    ],
                },
            },
        ]

        for test in data:
            result = Release.objects.get_released_stages(gateway, test["resource_version_ids"])
            assert result == test["expected"]

    def test_get_resource_version_released_stage_names(self, mocker):
        mocker.patch(
            "apigateway.core.managers.ReleaseManager.get_released_stages",
            return_value={
                1: [
                    {
                        "id": 1,
                        "name": "prod",
                    },
                    {
                        "id": 2,
                        "name": "test",
                    },
                ]
            },
        )
        result = Release.objects.get_resource_version_released_stage_names([1])
        assert result == {1: ["prod", "test"]}

    def test_save_release(self):
        gateway = G(Gateway)
        stage_1 = G(Stage, api=gateway)
        stage_2 = G(Stage, api=gateway)
        resource_version = G(ResourceVersion, api=gateway)
        G(Release, api=gateway, stage=stage_1, resource_version=resource_version)

        data = [
            {
                "stage_id": stage_1.id,
                "resource_version_id": resource_version.id,
            },
            {
                "stage_id": stage_2.id,
                "resource_version_id": resource_version.id,
            },
        ]
        for test in data:
            instance = Release.objects.save_release(
                gateway=gateway,
                stage=Stage.objects.get(id=test["stage_id"]),
                resource_version=ResourceVersion.objects.get(id=test["resource_version_id"]),
                comment="test",
                username="admin",
            )

            assert instance == Release.objects.get(stage__id=test["stage_id"])

    def test_get_released_resource_version_ids(self):
        gateway = G(Gateway)

        s1 = G(Stage, api=gateway, name="prod")
        s2 = G(Stage, api=gateway, name="test")

        rv1 = G(ResourceVersion, api=gateway)
        rv2 = G(ResourceVersion, api=gateway)

        G(Release, api=gateway, resource_version=rv1, stage=s1)
        G(Release, api=gateway, resource_version=rv2, stage=s2)

        result = Release.objects.get_released_resource_version_ids(gateway.id)
        assert result == [rv1.id, rv2.id]

        result = Release.objects.get_released_resource_version_ids(gateway.id, "prod")
        assert result == [rv1.id]

    def test_released_stage_names(self):
        gateway = G(Gateway)

        s1 = G(Stage, api=gateway, name="prod")
        s2 = G(Stage, api=gateway, name="test")

        rv1 = G(ResourceVersion, api=gateway)
        rv2 = G(ResourceVersion, api=gateway)

        G(Release, api=gateway, resource_version=rv1, stage=s1)
        G(Release, api=gateway, resource_version=rv2, stage=s2)

        result = Release.objects.get_released_stage_names(gateway.id)
        assert result == ["prod", "test"]

    def test_get_released_stage_count(self):
        gateway = G(Gateway)
        s1 = G(Stage, api=gateway)
        s2 = G(Stage, api=gateway)
        s3 = G(Stage, api=gateway)

        rv1 = G(ResourceVersion, api=gateway)
        rv2 = G(ResourceVersion, api=gateway)

        G(Release, api=gateway, resource_version=rv1, stage=s1)
        G(Release, api=gateway, resource_version=rv2, stage=s2)
        G(Release, api=gateway, resource_version=rv1, stage=s3)

        data = [
            {
                "params": {
                    "resource_version_ids": [rv1.id],
                },
                "expected": {
                    rv1.id: 2,
                },
            },
            {
                "params": {
                    "resource_version_ids": [rv1.id, rv2.id],
                },
                "expected": {
                    rv1.id: 2,
                    rv2.id: 1,
                },
            },
        ]
        for test in data:
            result = Release.objects.get_released_stage_count(**test["params"])
            assert result == test["expected"]

    def test_get_stage_id_to_fields_map(self):
        gateway = G(Gateway)
        s1 = G(Stage, api=gateway)
        s2 = G(Stage, api=gateway)
        s3 = G(Stage, api=gateway)

        rv1 = G(ResourceVersion, api=gateway)
        rv2 = G(ResourceVersion, api=gateway)

        G(Release, api=gateway, resource_version=rv1, stage=s1)
        G(Release, api=gateway, resource_version=rv2, stage=s2)
        G(Release, api=gateway, resource_version=rv1, stage=s3)

        data = [
            {
                "params": {
                    "gateway_id": gateway.id,
                    "resource_version_ids": [rv1.id],
                },
                "expected": {
                    s1.id: {
                        "stage_id": s1.id,
                        "resource_version_id": rv1.id,
                    },
                    s3.id: {
                        "stage_id": s3.id,
                        "resource_version_id": rv1.id,
                    },
                },
            },
            {
                "params": {
                    "gateway_id": gateway.id,
                    "resource_version_ids": [rv1.id, rv2.id],
                },
                "expected": {
                    s1.id: {
                        "stage_id": s1.id,
                        "resource_version_id": rv1.id,
                    },
                    s2.id: {
                        "stage_id": s2.id,
                        "resource_version_id": rv2.id,
                    },
                    s3.id: {
                        "stage_id": s3.id,
                        "resource_version_id": rv1.id,
                    },
                },
            },
        ]
        for test in data:
            result = Release.objects.get_stage_id_to_fields_map(**test["params"])
            assert result == test["expected"]

    def test_get_stage_ids_unreleased_the_version(self):
        gateway = G(Gateway)
        s1 = G(Stage, api=gateway)
        s2 = G(Stage, api=gateway)

        resource_version = G(ResourceVersion, api=gateway)
        G(Release, api=gateway, stage=s1, resource_version=resource_version)

        result = Release.objects.get_stage_ids_unreleased_the_version(gateway.id, [s1.id, s2.id], resource_version.id)
        assert result == [s2.id]

        result = Release.objects.get_stage_ids_unreleased_the_version(gateway.id, [s1.id], resource_version.id)
        assert result == []


class TestReleasedResourceManager:
    def test_clear_unreleased_resource(self):
        gateway = G(Gateway)

        s1 = G(Stage, api=gateway)

        rv1 = G(ResourceVersion, api=gateway)
        rv2 = G(ResourceVersion, api=gateway)

        G(Release, api=gateway, stage=s1, resource_version=rv1)

        G(ReleasedResource, api=gateway, resource_version_id=rv1.id, data={})
        G(ReleasedResource, api=gateway, resource_version_id=rv2.id, data={})

        ReleasedResource.objects.clear_unreleased_resource(gateway.id)

        assert ReleasedResource.objects.filter(resource_version_id=rv1.id).exists()
        assert not ReleasedResource.objects.filter(resource_version_id=rv2.id).exists()

    def test_get_resource_released_stage_count(self):
        gateway = G(Gateway)

        s1 = G(Stage, api=gateway)
        s2 = G(Stage, api=gateway)

        r1 = G(Resource, api=gateway)
        r2 = G(Resource, api=gateway)

        rv1 = G(ResourceVersion, api=gateway)
        rv2 = G(ResourceVersion, api=gateway)

        G(Release, api=gateway, stage=s1, resource_version=rv1)
        G(Release, api=gateway, stage=s2, resource_version=rv2)

        G(ReleasedResource, api=gateway, resource_version_id=rv1.id, resource_id=r1.id, data={})
        G(ReleasedResource, api=gateway, resource_version_id=rv1.id, resource_id=r2.id, data={})
        G(ReleasedResource, api=gateway, resource_version_id=rv2.id, resource_id=r2.id, data={})

        result = ReleasedResource.objects.get_resource_released_stage_count(
            gateway_id=gateway.id,
            resource_ids=[r1.id, r2.id],
        )
        assert result == {
            r1.id: 1,
            r2.id: 2,
        }

    def test_get_latest_released_resource(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)

        rv_1 = G(ResourceVersion, api=gateway)
        G(ResourceVersion, api=gateway)
        rv_3 = G(ResourceVersion, api=gateway)

        G(ReleasedResource, api=gateway, resource_id=resource.id, resource_version_id=rv_1.id, data={})
        G(
            ReleasedResource,
            api=gateway,
            resource_id=resource.id,
            resource_version_id=rv_3.id,
            data={
                "id": resource.id,
                "name": "test",
                "description": "desc",
                "method": "GET",
                "path": "/test",
                "match_subpath": False,
                "is_public": True,
                "contexts": {
                    "resource_auth": {
                        "config": json.dumps(
                            {
                                "resource_perm_required": True,
                                "app_verified_required": True,
                                "auth_verified_required": True,
                            }
                        ),
                    }
                },
            },
        )

        result = ReleasedResource.objects.get_latest_released_resource(gateway.id, resource.id)

        assert result == {
            "id": resource.id,
            "name": "test",
            "description": "desc",
            "description_en": "",
            "method": "GET",
            "path": "/test",
            "match_subpath": False,
            "is_public": True,
            "allow_apply_permission": True,
            "resource_perm_required": True,
            "app_verified_required": True,
            "user_verified_required": True,
            "disabled_stages": [],
        }

    def test_filter_latest_released_resources(self, fake_gateway):
        r1 = G(Resource, api=fake_gateway)
        r2 = G(Resource, api=fake_gateway)

        G(
            ReleasedResource,
            resource_id=r1.id,
            resource_version_id=1,
            api=fake_gateway,
            data={
                "id": r1.id,
                "name": "test1-1",
                "method": r1.method,
                "path": r1.path,
                "is_public": True,
                "contexts": {
                    "resource_auth": {
                        "config": json.dumps(
                            {
                                "resource_perm_required": True,
                                "app_verified_required": True,
                                "auth_verified_required": False,
                            }
                        )
                    }
                },
            },
        )
        G(
            ReleasedResource,
            resource_id=r1.id,
            resource_version_id=2,
            api=fake_gateway,
            data={
                "id": r1.id,
                "name": "test1-2",
                "method": r1.method,
                "path": r1.path,
                "is_public": True,
                "contexts": {
                    "resource_auth": {
                        "config": json.dumps(
                            {
                                "resource_perm_required": True,
                                "app_verified_required": True,
                                "auth_verified_required": False,
                            }
                        )
                    }
                },
            },
        )
        G(
            ReleasedResource,
            resource_id=r2.id,
            resource_version_id=2,
            api=fake_gateway,
            data={
                "id": r2.id,
                "name": "test2-1",
                "method": r2.method,
                "path": r2.path,
                "is_public": True,
                "contexts": {
                    "resource_auth": {
                        "config": json.dumps(
                            {
                                "resource_perm_required": True,
                                "app_verified_required": True,
                                "auth_verified_required": False,
                            }
                        )
                    }
                },
            },
        )

        result = ReleasedResource.objects.filter_latest_released_resources([r1.id, r2.id])

        assert len(result) == 2
        assert result[0]["name"] == "test1-2"
        assert result[1]["name"] == "test2-1"

    def test_get_latest_doc_link(self, mocker, settings, fake_gateway):
        def mocked_get_resource_doc_link(api_name, stage_name, resource_name):
            return f"{api_name}/{stage_name}/{resource_name}"

        mocker.patch(
            "apigateway.core.managers.get_resource_doc_link",
            side_effect=mocked_get_resource_doc_link,
        )

        fake_gateway.name = "test"
        fake_gateway.save()

        s1 = G(Stage, api=fake_gateway, name="prod", status=1)
        s2 = G(Stage, api=fake_gateway, name="dev", status=1)
        s3 = G(Stage, api=fake_gateway, name="test", status=1)

        r1 = G(Resource, api=fake_gateway, name="test1")
        r2 = G(Resource, api=fake_gateway, name="test2")
        r3 = G(Resource, api=fake_gateway, name="test3")
        r4 = G(Resource, api=fake_gateway, name="test4")

        rv1 = G(ResourceVersion, api=fake_gateway)
        rv2 = G(ResourceVersion, api=fake_gateway)

        G(Release, api=fake_gateway, resource_version=rv1, stage=s1)
        G(Release, api=fake_gateway, resource_version=rv1, stage=s2)
        G(Release, api=fake_gateway, resource_version=rv2, stage=s3)

        G(ReleasedResource, api=fake_gateway, resource_version_id=rv1.id, resource_id=r1.id, resource_name=r1.name)
        G(ReleasedResource, api=fake_gateway, resource_version_id=rv1.id, resource_id=r2.id, resource_name=r2.name)
        G(ReleasedResource, api=fake_gateway, resource_version_id=rv2.id, resource_id=r1.id, resource_name=r1.name)
        G(ReleasedResource, api=fake_gateway, resource_version_id=rv2.id, resource_id=r3.id, resource_name=r3.name)
        G(
            ReleasedResource,
            api=fake_gateway,
            resource_version_id=rv1.id,
            resource_id=r4.id,
            resource_name=r4.name,
            data={"disabled_stages": ["prod"]},
        )

        result = ReleasedResource.objects.get_latest_doc_link([r1.id, r2.id, r3.id, r4.id])

        assert result == {
            r1.id: "test/test/test1",
            r2.id: "test/prod/test2",
            r3.id: "test/test/test3",
            r4.id: "test/dev/test4",
        }

    def test_filter_resource_version_ids(self):
        fake_gateway = G(Gateway)

        r1 = G(Resource, api=fake_gateway)
        r2 = G(Resource, api=fake_gateway)

        rv1 = G(ResourceVersion, api=fake_gateway)
        rv2 = G(ResourceVersion, api=fake_gateway)

        G(ReleasedResource, api=fake_gateway, resource_version_id=rv1.id, resource_id=r1.id)
        G(ReleasedResource, api=fake_gateway, resource_version_id=rv1.id, resource_id=r2.id)

        result = ReleasedResource.objects._filter_resource_version_ids([r1.id, r2.id])
        assert result == [rv1.id]

    @pytest.mark.parametrize(
        "stage_names, disabled_stages, expecged",
        [
            (
                ["prod", "test"],
                [],
                "prod",
            ),
            (
                ["test", "dev"],
                [],
                "dev",
            ),
            (
                ["prod", "test"],
                ["prod"],
                "test",
            ),
            (
                ["prod", "test"],
                ["prod", "test"],
                None,
            ),
        ],
    )
    def test_get_recommended_stage_name(self, stage_names, disabled_stages, expecged):
        result = ReleasedResource.objects._get_recommended_stage_name(stage_names, disabled_stages)
        assert result == expecged


class TestReleaseHistoryManager(TestCase):
    def test_filter_release_history(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, api=gateway, name="prod")
        stage_test = G(Stage, api=gateway, name="test")
        resource_version_1 = G(ResourceVersion, api=gateway, name="test-20191225-aaaaa")
        resource_version_2 = G(ResourceVersion, api=gateway, name="test-20191225-bbbbb")

        history = G(ReleaseHistory, api=gateway, stage=stage_prod, resource_version=resource_version_1)
        history.stages.add(stage_prod)

        history = G(
            ReleaseHistory, api=gateway, stage=stage_prod, resource_version=resource_version_1, created_by="admin"
        )
        history.stages.add(stage_prod)

        history = G(
            ReleaseHistory,
            api=gateway,
            stage=stage_prod,
            resource_version=resource_version_1,
            created_time=dummy_time.time,
        )
        history.stages.add(stage_prod)

        history = G(ReleaseHistory, api=gateway, stage=stage_test, resource_version=resource_version_2)
        history.stages.add(stage_test)

        data = [
            # query, stage_name
            {
                "params": {
                    "query": "prod",
                },
                "expected": {
                    "count": 3,
                },
            },
            # query, release_version name
            {
                "params": {
                    "query": "aaaaa",
                },
                "expected": {
                    "count": 3,
                },
            },
            # stage prod
            {
                "params": {
                    "stage_id": stage_prod.id,
                },
                "expected": {
                    "count": 3,
                },
            },
            # created_by
            {
                "params": {
                    "created_by": "adm",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "time_start": dummy_time.time - datetime.timedelta(hours=1),
                    "time_end": dummy_time.time + datetime.timedelta(hours=1),
                },
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            result = ReleaseHistory.objects.filter_release_history(gateway, fuzzy=True, **test["params"])
            self.assertEqual(result.count(), test["expected"]["count"])

    def test_delete_without_stage_related(self):
        gateway = G(Gateway)
        stage_1 = G(Stage, api=gateway)
        stage_2 = G(Stage, api=gateway)

        history_1 = G(ReleaseHistory, api=gateway, stage=stage_1)
        history_2 = G(ReleaseHistory, api=gateway, stage=stage_2)
        history_2.stages.add(stage_2)

        ReleaseHistory.objects.delete_without_stage_related(gateway.id)

        self.assertFalse(ReleaseHistory.objects.filter(id=history_1.id).exists())


class TestJWTManager:
    def test_create_jwt(self):
        gateway = G(Gateway)
        data = [
            {
                "api": gateway,
            }
        ]
        for test in data:
            result = JWT.objects.create_jwt(test["api"])
            assert result.api == test["api"]
            assert result.private_key == ""
            assert "BEGIN PUBLIC KEY" in result.public_key
            assert result.encrypted_private_key

    def test_update_jwt_key(self, faker):
        gateway = G(Gateway)
        jwt = G(JWT, api=gateway, private_key=faker.pystr(), public_key=faker.pystr())

        JWT.objects.update_jwt_key(gateway, "test", "test")
        jwt = JWT.objects.get(api=gateway)

        cipher = AESCipherManager.create_jwt_cipher()
        assert jwt.public_key == "test"
        assert cipher.decrypt_from_hex(jwt.encrypted_private_key) == "test"

    def test_get_private_key(self):
        gateway = G(Gateway)
        jwt = G(JWT, api=gateway)
        JWT.objects.update_jwt_key(gateway, "test", "test")
        assert JWT.objects.get_private_key(gateway.id) == "test"

    def test_get_jwt(self):
        gateway = G(Gateway)
        jwt = JWT.objects.create_jwt(gateway)
        assert JWT.objects.get_jwt(gateway) == jwt

        gateway = G(Gateway)
        with pytest.raises(APIError):
            JWT.objects.get_jwt(gateway)

    def test_is_jwt_key_changed(self, faker):
        gateway = G(Gateway)
        jwt = JWT.objects.create_jwt(gateway)

        assert JWT.objects.is_jwt_key_changed(
            gateway,
            smart_bytes(faker.pystr()),
            smart_bytes(faker.pystr()),
        )

        cipher = AESCipherManager.create_jwt_cipher()
        assert not JWT.objects.is_jwt_key_changed(
            gateway,
            cipher.decrypt_from_hex(jwt.encrypted_private_key),
            smart_bytes(jwt.public_key),
        )


class TestAPIRelatedApp:
    def test_allow_app_manage_api(self, unique_id):
        gateway = G(Gateway)

        result = APIRelatedApp.objects.allow_app_manage_api(gateway.id, unique_id)
        assert result is False

        G(APIRelatedApp, api=gateway, bk_app_code=unique_id)
        result = APIRelatedApp.objects.allow_app_manage_api(gateway.id, unique_id)
        assert result is True

    def test_add_related_app(self):
        gateway = G(Gateway)

        APIRelatedApp.objects.add_related_app(gateway.id, "foo")
        assert APIRelatedApp.objects.filter(api_id=gateway.id).count() == 1

        APIRelatedApp.objects.add_related_app(gateway.id, "foo")
        assert APIRelatedApp.objects.filter(api_id=gateway.id).count() == 1

        APIRelatedApp.objects.add_related_app(gateway.id, "bar")
        assert APIRelatedApp.objects.filter(api_id=gateway.id).count() == 2

    def test_check_app_gateway_limit(self):
        APIRelatedApp.objects.all().delete()

        settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"]["bk_test"] = 1

        gateway = G(Gateway)
        APIRelatedApp.objects._check_app_gateway_limit("bk_test")

        APIRelatedApp.objects.add_related_app(gateway.id, "bk_test")
        with pytest.raises(APIError):
            APIRelatedApp.objects._check_app_gateway_limit("bk_test")

        del settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"]["bk_test"]
        APIRelatedApp.objects._check_app_gateway_limit("bk_test")

        APIRelatedApp.objects.all().delete()


class TestBackendServiceManager:
    def test_delete_backend_service(self, fake_gateway):
        backend_service = G(BackendService, api=fake_gateway)
        proxy = G(Proxy, backend_service=backend_service)

        with pytest.raises(InstanceDeleteError):
            BackendService.objects.delete_backend_service(backend_service.id)

        proxy.delete()
        BackendService.objects.delete_backend_service(backend_service.id)
        assert not BackendService.objects.filter(api=fake_gateway).exists()


class TestSslCertificateManager:
    def test_delete_by_id(self, fake_gateway):
        ssl_certificate = G(SslCertificate, api=fake_gateway)
        related = G(
            SslCertificateBinding,
            api=fake_gateway,
            scope_type=SSLCertificateBindingScopeTypeEnum.STAGE_ITEM_CONFIG.value,
            scope_id=1,
            ssl_certificate=ssl_certificate,
        )

        with pytest.raises(InstanceDeleteError):
            SslCertificate.objects.delete_by_id(ssl_certificate.id)

        related.delete()
        SslCertificate.objects.delete_by_id(ssl_certificate.id)
        assert not SslCertificate.objects.filter(api=fake_gateway).exists()

    def test_get_valid_ids(self, fake_ssl_certificate):
        result = SslCertificate.objects.get_valid_ids(
            gateway_id=fake_ssl_certificate.api.id,
            ids=[fake_ssl_certificate.id, 0],
        )
        assert result == [fake_ssl_certificate.id]

    def test_get_valid_id(self, fake_ssl_certificate):
        result = SslCertificate.objects.get_valid_id(
            gateway_id=fake_ssl_certificate.api.id,
            id_=fake_ssl_certificate.id,
        )
        assert result == fake_ssl_certificate.id

        result = SslCertificate.objects.get_valid_id(
            gateway_id=fake_ssl_certificate.api.id,
            id_=0,
        )
        assert result is None


class TestSslCertificateBindingManager:
    def test_get_valid_scope_id(self, fake_ssl_certificate_binding):
        result = SslCertificateBinding.objects.get_valid_scope_id(
            gateway_id=fake_ssl_certificate_binding.api.id,
            scope_type=fake_ssl_certificate_binding.scope_type,
            scope_id=fake_ssl_certificate_binding.scope_id,
        )
        assert result == fake_ssl_certificate_binding.scope_id

        result = SslCertificateBinding.objects.get_valid_scope_id(
            gateway_id=fake_ssl_certificate_binding.api.id,
            scope_type=fake_ssl_certificate_binding.scope_type,
            scope_id=0,
        )
        assert result is None


class TestStageItemManager:
    def delete_stage_item(self, fake_gateway):
        stage_item = G(StageItem, api=fake_gateway)
        backend_service = G(BackendService, api=fake_gateway, stage_item=stage_item)

        with pytest.raises(InstanceDeleteError):
            StageItem.objects.delete_stage_item(stage_item.id)

        backend_service.delete()
        StageItem.objects.delete_stage_item(stage_item.id)
        assert not StageItem.objects.filter(api=fake_gateway).exists()

    def test_get_reference_instances(self, fake_gateway):
        item = G(StageItem, api=fake_gateway)
        result = StageItem.objects.get_reference_instances(fake_gateway.id)
        assert result == {}

        G(BackendService, api=fake_gateway, stage_item=item)
        result = StageItem.objects.get_reference_instances(fake_gateway.id)
        assert len(result[item.id]) == 1

        G(BackendService, api=fake_gateway)
        result = StageItem.objects.get_reference_instances(fake_gateway.id)
        assert len(result[item.id]) == 1


class TestStageItemConfigManager:
    def test_get_configured_item_ids(self, fake_stage):
        fake_gateway = fake_stage.api

        stage_item1 = G(StageItem, api=fake_gateway)
        G(StageItem, api=fake_gateway)
        G(StageItemConfig, api=fake_gateway, stage=fake_stage, stage_item=stage_item1)

        result = StageItemConfig.objects.get_configured_item_ids(fake_gateway.id, fake_stage.id)
        assert result == set([stage_item1.id])

    def test_get_stage_item_id_to_configured_stages(self, fake_gateway):
        result = StageItemConfig.objects.get_stage_item_id_to_configured_stages(fake_gateway.id)
        assert result == {}

        s1 = G(Stage, api=fake_gateway)
        G(Stage, api=fake_gateway)
        item = G(StageItem, api=fake_gateway)
        G(StageItemConfig, api=fake_gateway, stage=s1, stage_item=item)

        result = StageItemConfig.objects.get_stage_item_id_to_configured_stages(fake_gateway.id)
        assert result == {item.id: [{"id": s1.id, "name": s1.name}]}

    def test_get_configs(self, fake_stage_item_config):
        result = StageItemConfig.objects.get_configs(
            gateway_id=fake_stage_item_config.api.id,
            stage_item_id=fake_stage_item_config.stage_item.id,
        )
        stage = fake_stage_item_config.stage
        assert result == [
            {
                "stage_id": stage.id,
                "stage_name": stage.name,
                "config": {"nodes": [{"host": "1.0.0.1", "weight": 100}]},
            }
        ]


class TestMicroGatewayManager:
    def test_get_count_by_gateway(self, fake_gateway):
        G(MicroGateway, api=fake_gateway)
        G(MicroGateway, api=fake_gateway)

        result = MicroGateway.objects.get_count_by_gateway([fake_gateway.id])
        assert result == {fake_gateway.id: 2}
