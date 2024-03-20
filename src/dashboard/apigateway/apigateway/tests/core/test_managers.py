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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.biz.stage import StageHandler
from apigateway.core import constants
from apigateway.core.constants import (
    StageStatusEnum,
)
from apigateway.core.models import (
    Gateway,
    MicroGateway,
    Release,
    ReleasedResource,
    ReleaseHistory,
    Resource,
    ResourceVersion,
    Stage,
)
from apigateway.tests.utils.testing import dummy_time

pytestmark = pytest.mark.django_db


class TestStageManager:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    def test_get_stage_ids(self):
        gateway = G(Gateway)
        s1 = G(Stage, gateway=gateway)
        s2 = G(Stage, gateway=gateway)

        result = Stage.objects.get_ids(gateway.id)
        assert sorted(result) == [s1.id, s2.id]

    def test_get_name_id_map(self):
        gateway = G(Gateway)
        s1 = G(Stage, gateway=gateway, name="prod")
        s2 = G(Stage, gateway=gateway, name="test")

        result = Stage.objects.get_name_id_map(gateway)
        assert result == {"prod": s1.id, "test": s2.id}

    def test_create_stage(self):
        gateway = G(Gateway)
        data = [
            {
                "gateway": gateway,
                "created_by": "admin",
            }
        ]
        for test in data:
            result = StageHandler().create_default(
                test["gateway"],
                created_by=test["created_by"],
            )
            assert result.gateway == test["gateway"]
            assert result.name == "prod"
            assert result.vars == {}
            assert result.status == constants.StageStatusEnum.INACTIVE.value
            assert result.created_by == test["created_by"]

    def test_get_micro_gateway_id_to_fields(self):
        gateway = G(Gateway)

        micro_gateway = G(MicroGateway, gateway=gateway)

        G(Stage, gateway=gateway)
        s2 = G(Stage, gateway=gateway, micro_gateway=micro_gateway)

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

        s1 = G(Stage, gateway=gateway, name="s1", status=StageStatusEnum.ACTIVE.value)
        s2 = G(Stage, gateway=gateway, name="s2", status=StageStatusEnum.INACTIVE.value)
        s3 = G(Stage, gateway=gateway, name="s3", status=StageStatusEnum.ACTIVE.value)

        result = Stage.objects.get_gateway_name_to_active_stage_names([gateway])
        assert result == {gateway.name: ["s1", "s3"]}

    def test_get_name(self, fake_gateway):
        s = G(Stage, gateway=fake_gateway)

        name = Stage.objects.get_name(fake_gateway.id, s.id)
        assert name == s.name

        name = Stage.objects.get_name(fake_gateway.id, 0)
        assert name is None


class TestResourceVersionManager:
    def test_get_id_to_fields_map(self):
        gateway = G(Gateway)
        rv1 = G(ResourceVersion, gateway=gateway, name="rv1", title="rv1", version="1.0.1")
        rv2 = G(ResourceVersion, gateway=gateway, name="rv2", title="rv2", version="1.0.2")

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

        resource_version = G(ResourceVersion, gateway=gateway, name=unique_id)
        result = ResourceVersion.objects.get_id_by_name(gateway, unique_id)
        assert result == resource_version.id

    def test_get_id_by_version(self, unique_id):
        gateway = G(Gateway)

        result = ResourceVersion.objects.get_id_by_version(gateway, unique_id)
        assert result is None

        resource_version = G(ResourceVersion, gateway=gateway, version=unique_id)
        result = ResourceVersion.objects.get_id_by_version(gateway, unique_id)
        assert result == resource_version.id

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
                    fake_resource_version.gateway.id,
                    version=fake_resource_version.version,
                )
            )
            == expected
        )


class TestReleaseManager:
    def test_get_released_stages(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, gateway=gateway, name="prod", status=1)
        stage_test = G(Stage, gateway=gateway, name="test", status=1)
        stage_dev = G(Stage, gateway=gateway, name="dev", status=1)
        resource_version_1 = G(ResourceVersion, gateway=gateway)
        resource_version_2 = G(ResourceVersion, gateway=gateway)
        G(Release, gateway=gateway, stage=stage_prod, resource_version=resource_version_1)
        G(Release, gateway=gateway, stage=stage_dev, resource_version=resource_version_2)
        G(Release, gateway=gateway, stage=stage_test, resource_version=resource_version_1)

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
        stage_1 = G(Stage, gateway=gateway)
        stage_2 = G(Stage, gateway=gateway)
        resource_version = G(ResourceVersion, gateway=gateway)
        G(Release, gateway=gateway, stage=stage_1, resource_version=resource_version)

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

        s1 = G(Stage, gateway=gateway, name="prod")
        s2 = G(Stage, gateway=gateway, name="test")

        rv1 = G(ResourceVersion, gateway=gateway)
        rv2 = G(ResourceVersion, gateway=gateway)

        G(Release, gateway=gateway, resource_version=rv1, stage=s1)
        G(Release, gateway=gateway, resource_version=rv2, stage=s2)

        result = Release.objects.get_released_resource_version_ids(gateway.id)
        assert result == [rv1.id, rv2.id]

        result = Release.objects.get_released_resource_version_ids(gateway.id, "prod")
        assert result == [rv1.id]


class TestReleasedResourceManager:
    def test_filter_latest_released_resources(self, fake_gateway):
        r1 = G(Resource, gateway=fake_gateway)
        r2 = G(Resource, gateway=fake_gateway)

        G(
            ReleasedResource,
            resource_id=r1.id,
            resource_version_id=1,
            gateway=fake_gateway,
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
            gateway=fake_gateway,
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
            gateway=fake_gateway,
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

    def test_filter_resource_version_ids(self):
        fake_gateway = G(Gateway)

        r1 = G(Resource, gateway=fake_gateway)
        r2 = G(Resource, gateway=fake_gateway)

        rv1 = G(ResourceVersion, gateway=fake_gateway)
        rv2 = G(ResourceVersion, gateway=fake_gateway)

        G(ReleasedResource, gateway=fake_gateway, resource_version_id=rv1.id, resource_id=r1.id)
        G(ReleasedResource, gateway=fake_gateway, resource_version_id=rv1.id, resource_id=r2.id)

        result = ReleasedResource.objects.filter_resource_version_ids([r1.id, r2.id])
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
        result = ReleasedResource.objects.get_recommended_stage_name(stage_names, disabled_stages)
        assert result == expecged


class TestReleaseHistoryManager(TestCase):
    def test_filter_release_history(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, gateway=gateway, name="prod")
        stage_test = G(Stage, gateway=gateway, name="test")
        resource_version_1 = G(ResourceVersion, gateway=gateway, name="test-20191225-aaaaa")
        resource_version_2 = G(ResourceVersion, gateway=gateway, name="test-20191225-bbbbb")

        history = G(ReleaseHistory, gateway=gateway, stage=stage_prod, resource_version=resource_version_1)

        history = G(
            ReleaseHistory, gateway=gateway, stage=stage_prod, resource_version=resource_version_1, created_by="admin"
        )

        history = G(
            ReleaseHistory,
            gateway=gateway,
            stage=stage_prod,
            resource_version=resource_version_1,
            created_time=dummy_time.time,
        )

        history = G(ReleaseHistory, gateway=gateway, stage=stage_test, resource_version=resource_version_2)

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
