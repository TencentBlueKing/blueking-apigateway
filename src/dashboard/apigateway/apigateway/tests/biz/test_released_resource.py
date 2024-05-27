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

import pytest
from ddf import G

from apigateway.biz.released_resource import (
    ReleasedResourceData,
    ReleasedResourceHandler,
    get_released_resource_data,
)
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.tests.utils.testing import dummy_time

pytestmark = pytest.mark.django_db


class TestReleasedResource:
    @pytest.mark.parametrize(
        "config, expected",
        [
            (
                {},
                {
                    "verified_user_required": False,
                    "resource_perm_required": False,
                },
            ),
            (
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "resource_perm_required": False,
                },
                {
                    "verified_user_required": False,
                    "resource_perm_required": False,
                },
            ),
            (
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": True,
                    "resource_perm_required": True,
                },
                {
                    "verified_user_required": True,
                    "resource_perm_required": True,
                },
            ),
            (
                {
                    "skip_auth_verification": True,
                    "auth_verified_required": True,
                    "resource_perm_required": True,
                },
                {
                    "verified_user_required": False,
                    "resource_perm_required": True,
                },
            ),
        ],
    )
    def test_init(self, config, expected):
        data = ReleasedResourceData(
            id=1,
            name="foo",
            method="GET",
            path="/foo",
            match_subpath=False,
            contexts={"resource_auth": {"config": json.dumps(config)}},
        )
        assert data.verified_user_required == expected["verified_user_required"]
        assert data.resource_perm_required == expected["resource_perm_required"]

    def test_get_released_resource_data(self, fake_gateway, fake_stage, fake_resource1, fake_released_resource):
        result = get_released_resource_data(fake_gateway, fake_stage, fake_resource1.id)
        assert result is not None

        # resource_version_id is None
        result = get_released_resource_data(G(Gateway), fake_stage, fake_resource1.id)
        assert result is None

        # released_resource is None
        result = get_released_resource_data(fake_gateway, fake_stage, 0)
        assert result is None


class TestReleasedResourceHandler:
    def test_clear_unreleased_resource(self, fake_gateway, fake_stage):
        rv1 = G(ResourceVersion, gateway=fake_gateway)
        rv2 = G(ResourceVersion, gateway=fake_gateway)

        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv1)

        G(ReleasedResource, gateway=fake_gateway, resource_version_id=rv1.id, data={})
        G(ReleasedResource, gateway=fake_gateway, resource_version_id=rv2.id, data={})

        ReleasedResourceHandler.clear_unreleased_resource(fake_gateway.id)

        assert ReleasedResource.objects.filter(resource_version_id=rv1.id).exists()
        assert not ReleasedResource.objects.filter(resource_version_id=rv2.id).exists()

    def test_get_stage_release(self, fake_gateway):
        stage_prod = G(Stage, gateway=fake_gateway, name="prod", status=1)
        stage_test = G(Stage, gateway=fake_gateway, name="test", status=1)

        resource_version = G(ResourceVersion, gateway=fake_gateway, name="test-01", title="test", version="1.0.1")
        G(
            Release,
            gateway=fake_gateway,
            stage=stage_prod,
            resource_version=resource_version,
            updated_by="test",
            updated_time=dummy_time.time,
        )

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
                        "resource_version_display": "1.0.1",
                        "resource_version": {
                            "version": "1.0.1",
                        },
                        "resource_version_schema_version": "1.0",
                        "release_by": "test",
                    },
                },
            }
        ]
        for test in data:
            result = ReleasedResourceHandler.get_stage_release(fake_gateway, test["stage_ids"])
            assert result == test["expected"]

    def test_get_public_released_resource_data_list(self, fake_gateway, fake_stage, fake_release):
        result = ReleasedResourceHandler.get_public_released_resource_data_list(fake_gateway.id, fake_stage.name)
        assert len(result) >= 1

        result = ReleasedResourceHandler.get_public_released_resource_data_list(fake_gateway.id, "")
        assert len(result) == 0

    def test_get_released_resource(self, fake_gateway, fake_stage, fake_released_resource):
        result = ReleasedResourceHandler.get_released_resource(
            fake_gateway.id, "", fake_released_resource.resource_name
        )
        assert result is None

        result = ReleasedResourceHandler.get_released_resource(fake_gateway.id, fake_stage.name, "")
        assert result is None

        result = ReleasedResourceHandler.get_released_resource(
            fake_gateway.id, fake_stage.name, fake_released_resource.resource_name
        )
        assert result
        assert isinstance(result, ReleasedResource)
