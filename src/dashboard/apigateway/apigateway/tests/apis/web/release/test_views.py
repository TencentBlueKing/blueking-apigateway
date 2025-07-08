# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from unittest.mock import MagicMock

import pytest
from django_dynamic_fixture import G
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from openapi_schema_to_json_schema import to_json_schema

from apigateway.apps.openapi.models import OpenAPIResourceSchemaVersion
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.service.contexts import StageProxyHTTPContext
from apigateway.tests.utils.testing import create_gateway, dummy_time

pytestmark = pytest.mark.django_db


class TestReleaseCreateApi:
    def test_release_with_hosts(
        self, request_view, fake_admin_user, mocker, fake_gateway, fake_resource_version, fake_shared_gateway
    ):
        """Test release API with different hosts config of stage objects."""
        stage_1 = G(Stage, gateway=fake_gateway, name="prod", status=0)
        stage_2 = G(Stage, gateway=fake_gateway, name="test", status=0)
        resource_version = G(ResourceVersion, gateway=fake_gateway, _data=json.dumps([]))
        G(Release, gateway=fake_gateway, stage=stage_1, resource_version=resource_version)

        mocker.patch("apigateway.apis.web.release.views.Lock", return_value=MagicMock())

        # Config a valid hosts config for each stages
        for stage in [stage_1, stage_2]:
            StageProxyHTTPContext().save(
                stage.id,
                config={
                    "upstreams": {"hosts": [{"host": "https://example.com"}], "loadbalance": "roundrobin"},
                    "timeout": 60,
                    "transform_headers": {},
                },
            )

        for stage in [stage_1, stage_2]:
            release_history = G(
                ReleaseHistory,
                gateway=fake_gateway,
                stage=stage,
                resource_version=fake_resource_version,
                created_time=dummy_time.time,
            )
            # TODO: mock the releaser
            mocker.patch("apigateway.apis.web.release.views.release", return_value=release_history)

            data = {
                "gateway_id": fake_gateway.id,
                "stage_id": stage.id,
                "resource_version_id": resource_version.id,
            }
            resp = request_view(
                method="POST",
                view_name="gateway.release.create",
                gateway=fake_gateway,
                path_params={"gateway_id": fake_gateway.id},
                data=data,
                user=fake_admin_user,
            )

            result = resp.json()

            # There should be one history record for both cases.
            history_qs = ReleaseHistory.objects.filter(stage_id=data["stage_id"]).distinct()
            assert history_qs.count() == 1

            assert resp.status_code == 200, result


class TestReleaseAvailableResourceListApi:
    def test_list(self, request_view, fake_gateway, fake_stage):
        stage_1 = G(Stage, gateway=fake_gateway, name="prod", status=0)
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            _data=json.dumps(
                [
                    {
                        "id": 1,
                        "name": "test",
                        "method": "get",
                        "path": "/test/",
                        "description": "test...",
                        "description_en": "",
                        "match_subpath": "",
                        "is_public": True,
                        "allow_apply_permission": True,
                        "disabled_stages": [],
                        "contexts": {
                            "resource_auth": {
                                "config": json.dumps(
                                    {
                                        "app_verified_required": True,
                                        "skip_auth_verification": True,
                                        "auth_verified_required": True,
                                        "resource_perm_required": True,
                                    }
                                )
                            }
                        },
                        "api_labels": "",
                    }
                ]
            ),
        )

        G(Release, gateway=fake_gateway, stage=stage_1, resource_version=resource_version)

        response = request_view(
            method="GET",
            view_name="gateway.releases.available_resources",
            path_params={"gateway_id": fake_gateway.id, "stage_id": stage_1.id},
        )

        result = response.json()

        assert response.status_code == 200
        assert result == {
            "data": [
                {
                    "id": 1,
                    "name": "test",
                    "description": "test...",
                    "method": "get",
                    "path": "/test/",
                    "verified_user_required": False,
                    "verified_app_required": True,
                    "resource_perm_required": True,
                    "is_public": True,
                    "labels": [],
                }
            ]
        }


class TestReleaseResourceSchemaRetrieve:
    def test_retry(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_release,
        fake_resource,
        fake_resource_version,
        fake_resource_schema_with_body,
        request_factory,
    ):
        openapi_schema_version = G(
            OpenAPIResourceSchemaVersion,
            resource_version=fake_resource_version,
            schema=[
                {
                    "resource_id": fake_resource.id,
                    "schema": fake_resource_schema_with_body.schema,
                }
            ],
        )

        resp = request_view(
            method="GET",
            view_name="gateway.releases.available_resource.schema",
            path_params={"gateway_id": fake_gateway.id, "stage_id": fake_stage.id, "resource_id": fake_resource.id},
        )
        result = resp.json()
        assert result["data"]["body_schema"] == fake_resource_schema_with_body.schema["requestBody"]

        json_schema = to_json_schema(
            fake_resource_schema_with_body.schema["requestBody"]["content"]["application/json"]["schema"]
        )

        # 验证生成的示例数据是否符合 JSON Schema
        try:
            validate(instance=result["data"]["body_example"], schema=json_schema)
        except ValidationError as e:
            pytest.fail(f"Example data is invalid: {e}")


class TestReleaseHistoryListApi:
    def test_list(self, request_view, fake_gateway, request_factory):
        stage_1 = G(Stage, gateway=fake_gateway, name="test-01")
        stage_2 = G(Stage, gateway=fake_gateway)

        resource_version = G(ResourceVersion, gateway=fake_gateway)

        history = G(ReleaseHistory, gateway=fake_gateway, stage=stage_1, resource_version=resource_version)

        history = G(
            ReleaseHistory, gateway=fake_gateway, stage=stage_2, resource_version=resource_version, created_by="admin"
        )

        data = [
            {
                "keyword": "test",
                "expected": {
                    "count": 1,
                },
            },
            {
                "stage_id": stage_1.id,
                "expected": {
                    "count": 1,
                },
            },
            {
                "created_by": "admin",
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            resp = request_view(
                method="GET",
                view_name="gateway.release_histories.list",
                path_params={"gateway_id": fake_gateway.id},
                data=test,
            )

            result = resp.json()
            assert result["data"]["count"] == test["expected"]["count"]


class TestReleaseHistoryRetrieveApi:
    def test_retrieve_latest(self, request_view, fake_gateway):
        stage = G(Stage, gateway=fake_gateway)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        G(ReleaseHistory, gateway=fake_gateway, created_time=dummy_time.time)
        history = G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=stage,
            resource_version=resource_version,
            created_time=dummy_time.time,
        )

        event_1 = G(
            PublishEvent,
            publish=history,
            name=PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value,
            status=PublishEventStatusTypeEnum.FAILURE.value,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
        )

        gateway_2 = create_gateway()

        data = [
            {
                "gateway": fake_gateway,
                "expected": {
                    "id": history.id,
                    "stage": {"id": stage.id, "name": stage.name},
                    "created_time": dummy_time.str,
                    "resource_version_display": resource_version.object_display,
                    "created_by": history.created_by,
                    "source": history.source,
                    "status": f"{event_1.status}",
                    "duration": (event_1.created_time - history.created_time).total_seconds(),
                },
            },
            {
                "gateway": gateway_2,
                "expected": {},
            },
        ]
        for test in data:
            resp = request_view(
                method="GET",
                view_name="gateway.release_histories.retrieve_latest",
                path_params={"gateway_id": test["gateway"].id},
                data=test,
            )

            result = resp.json()
            assert result["data"] == test["expected"]


class TestReleaseHistoryEventsRetrieveAPI:
    def test_retrieve(self, request_view, fake_gateway):
        stage = G(Stage, gateway=fake_gateway)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        G(ReleaseHistory, gateway=fake_gateway, created_time=dummy_time.time)
        history = G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=stage,
            resource_version=resource_version,
            created_time=dummy_time.time,
        )

        event_1 = G(
            PublishEvent,
            publish=history,
            name=PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value,
            status=PublishEventStatusTypeEnum.FAILURE.value,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
        )

        resp = request_view(
            method="GET",
            view_name="gateway.release_histories.events",
            path_params={"gateway_id": fake_gateway.id, "history_id": history.id},
        )

        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) >= 1
