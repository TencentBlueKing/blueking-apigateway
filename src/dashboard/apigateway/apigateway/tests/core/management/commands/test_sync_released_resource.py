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
from io import StringIO

import pytest
from ddf import G
from django.core.management import call_command

from apigateway.core.models import Release, ReleasedResource, ResourceVersion, Stage

pytestmark = pytest.mark.django_db


def _resource(resource_id, user_required, app_required):
    return {
        "id": resource_id,
        "name": f"resource-{resource_id}",
        "method": "GET",
        "path": f"/r{resource_id}",
        "is_public": True,
        "contexts": {
            "resource_auth": {
                "config": json.dumps({"auth_verified_required": user_required, "app_verified_required": app_required})
            }
        },
    }


class TestOAuth2AppFlags:
    def test_refreshes_stale_rows_and_creates_missing_projection(self, fake_gateway, fake_stage):
        stale_version = G(ResourceVersion, gateway=fake_gateway)
        stale_version.data = [_resource(1, True, True), _resource(2, False, True)]
        stale_version.save()
        ReleasedResource.objects.save_released_resource(stale_version)
        ReleasedResource.objects.filter(resource_version_id=stale_version.id).update(
            oauth2_app_delegated_enabled=False, oauth2_app_only_enabled=False
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=stale_version)

        missing_version = G(ResourceVersion, gateway=fake_gateway)
        missing_version.data = [_resource(3, True, True)]
        missing_version.save()
        G(Release, gateway=fake_gateway, stage=G(Stage, gateway=fake_gateway), resource_version=missing_version)

        stdout = StringIO()
        call_command("sync_released_resource", "--gateway-id", fake_gateway.id, "--oauth2-app-flags", stdout=stdout)

        flags = {
            row.resource_id: (row.oauth2_app_delegated_enabled, row.oauth2_app_only_enabled)
            for row in ReleasedResource.objects.filter(gateway=fake_gateway)
        }
        assert flags == {1: (True, False), 2: (False, True), 3: (True, False)}
        assert "refreshed 2 rows" in stdout.getvalue()

        stdout = StringIO()
        call_command("sync_released_resource", "--gateway-id", fake_gateway.id, "--oauth2-app-flags", stdout=stdout)
        assert "refreshed 0 rows" in stdout.getvalue()

    def test_dry_run_does_not_write(self, fake_gateway, fake_stage):
        version = G(ResourceVersion, gateway=fake_gateway)
        version.data = [_resource(1, True, True)]
        version.save()
        ReleasedResource.objects.save_released_resource(version)
        ReleasedResource.objects.filter(resource_version_id=version.id).update(oauth2_app_delegated_enabled=False)
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=version)

        stdout = StringIO()
        call_command(
            "sync_released_resource", "--gateway-id", fake_gateway.id, "--oauth2-app-flags", "--dry-run", stdout=stdout
        )

        assert "would refresh 1 rows" in stdout.getvalue()
        assert ReleasedResource.objects.get(resource_version_id=version.id).oauth2_app_delegated_enabled is False
