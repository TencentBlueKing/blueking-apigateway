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
import json

import pytest
from django_dynamic_fixture import G

from apigateway.biz.stage import StageHandler
from apigateway.core import constants
from apigateway.core.constants import (
    GatewayKindEnum,
    StageStatusEnum,
)
from apigateway.core.models import (
    Gateway,
    Release,
    ReleasedResource,
    Resource,
    ResourceVersion,
    Stage,
)

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

        result = Stage.objects.get_name_id_map(gateway.id)
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

    def test_create_stage_of_programmable_gateway(self):
        gateway = G(Gateway, kind=GatewayKindEnum.PROGRAMMABLE.value)
        result = StageHandler().create_default(
            gateway,
            created_by="admin",
        )
        assert result.gateway == gateway
        # there should be two stages, one is prod, one is stag
        assert Stage.objects.filter(gateway=gateway).count() == 2
        assert Stage.objects.filter(gateway=gateway, name="prod").exists()
        assert Stage.objects.filter(gateway=gateway, name="stag").exists()

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
    def test_get_resources_defaults_missing_kind_to_standard(self, fake_resource_version_v2):
        data = fake_resource_version_v2.data
        resource_id = data[0]["id"]
        data[0].pop("kind", None)
        fake_resource_version_v2.data = data
        fake_resource_version_v2.save(update_fields=["_data"])
        ResourceVersion.objects.get_resources.cache_clear()

        resources = ResourceVersion.objects.get_resources(
            fake_resource_version_v2.gateway_id,
            fake_resource_version_v2.id,
        )

        assert resources[resource_id]["kind"] == constants.ResourceKindEnum.STANDARD.value
        ResourceVersion.objects.get_resources.cache_clear()

    def test_get_id_to_fields_map(self):
        gateway = G(Gateway)
        rv1 = G(ResourceVersion, gateway=gateway, version="1.0.1")
        rv2 = G(ResourceVersion, gateway=gateway, version="1.0.2")

        data = [
            {
                "params": {
                    "gateway_id": gateway.id,
                    "resource_version_ids": None,
                },
                "expected": {
                    rv1.id: {"id": rv1.id, "version": "1.0.1"},
                    rv2.id: {"id": rv2.id, "version": "1.0.2"},
                },
            },
            {
                "params": {
                    "gateway_id": gateway.id,
                    "resource_version_ids": [rv1.id],
                },
                "expected": {
                    rv1.id: {"id": rv1.id, "version": "1.0.1"},
                },
            },
        ]
        for test in data:
            result = ResourceVersion.objects.get_id_to_fields_map(**test["params"])
            assert result == test["expected"]

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
        stage_offline = G(Stage, gateway=gateway, name="offline", status=StageStatusEnum.INACTIVE.value)
        resource_version_1 = G(ResourceVersion, gateway=gateway)
        resource_version_2 = G(ResourceVersion, gateway=gateway)
        G(Release, gateway=gateway, stage=stage_prod, resource_version=resource_version_1)
        G(Release, gateway=gateway, stage=stage_dev, resource_version=resource_version_2)
        G(Release, gateway=gateway, stage=stage_test, resource_version=resource_version_1)
        G(Release, gateway=gateway, stage=stage_offline, resource_version=resource_version_1)

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

    def test_get_released_stage_names_by_resource_versions(self):
        gateway = G(Gateway)
        other_gateway = G(Gateway)
        resource_version_1 = G(ResourceVersion, gateway=gateway)
        resource_version_2 = G(ResourceVersion, gateway=gateway)

        stage_test = G(Stage, gateway=gateway, name="test", status=StageStatusEnum.ACTIVE.value)
        stage_prod = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        stage_offline = G(Stage, gateway=gateway, name="offline", status=StageStatusEnum.INACTIVE.value)
        stage_other = G(Stage, gateway=other_gateway, name="other", status=StageStatusEnum.ACTIVE.value)

        G(Release, gateway=gateway, stage=stage_test, resource_version=resource_version_1)
        G(Release, gateway=gateway, stage=stage_prod, resource_version=resource_version_2)
        G(Release, gateway=gateway, stage=stage_offline, resource_version=resource_version_1)
        G(Release, gateway=other_gateway, stage=stage_other, resource_version=resource_version_1)

        result = Release.objects.get_released_stage_names_by_resource_versions(
            gateway.id, [resource_version_1.id, resource_version_2.id]
        )
        assert result == ["prod", "test"]

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
            instance = Release.objects.get_or_create_release(
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
