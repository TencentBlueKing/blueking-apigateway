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

import pytest
from django_dynamic_fixture import G

from apigateway.apps.release.views import ReleaseHistoryViewSet
from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, dummy_time, get_response_json

pytestmark = pytest.mark.django_db


class TestReleaseBatchViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, request_factory):
        self.factory = request_factory

    @pytest.mark.parametrize(
        "configure_hosts,succeeded",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_release_with_hosts(self, configure_hosts, succeeded, fake_admin_user, request_view, mocker, fake_gateway):
        """Test release API with different hosts config of stage objects."""
        mocker.patch(
            "apigateway.apps.release.releasers.reversion_update_signal.send",
            return_value=None,
        )

        stage_1 = G(Stage, api=fake_gateway, name="prod", status=0)
        stage_2 = G(Stage, api=fake_gateway, name="test", status=0)
        resource_version = G(ResourceVersion, api=fake_gateway, _data=json.dumps([]))
        G(Release, api=fake_gateway, stage=stage_1, resource_version=resource_version)

        if configure_hosts:
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

        data = {
            "api_id": fake_gateway.id,
            "stage_ids": [stage_1.id, stage_2.id],
            "resource_version_id": resource_version.id,
        }

        self.factory.post(f"/apis/{fake_gateway.id}/releases/batch/", data=data)

        response = request_view(
            "POST",
            "apigateway.apps.releases.batch",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data=data,
            user=fake_admin_user,
        )

        result = get_response_json(response)

        # There should be one history record for both cases.
        history_qs = ReleaseHistory.objects.filter(stages__id__in=data["stage_ids"]).distinct()
        assert history_qs.count() == 1

        if not succeeded:
            assert history_qs[0].status == ReleaseStatusEnum.FAILURE.value
            assert result["code"] != 0, result
        else:
            # The request finished successfully
            assert history_qs[0].status == ReleaseStatusEnum.SUCCESS.value
            assert result["code"] == 0, result

            for stage_id in data["stage_ids"]:
                release = Release.objects.get(stage__id=stage_id)
                assert release.resource_version == resource_version


class TestReleaseHistoryViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = create_gateway()

    def test_list(self, request_factory):
        stage_1 = G(Stage, api=self.gateway, name="test-01")
        stage_2 = G(Stage, api=self.gateway)

        resource_version = G(ResourceVersion, api=self.gateway)

        history = G(ReleaseHistory, api=self.gateway, stage=stage_1, resource_version=resource_version)
        history.stages.add(stage_1)

        history = G(
            ReleaseHistory, api=self.gateway, stage=stage_2, resource_version=resource_version, created_by="admin"
        )
        history.stages.add(stage_2)

        data = [
            {
                "query": "test",
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
            request = request_factory.get(f"/apis/{self.gateway.id}/releases/histories/", data=test)

            view = ReleaseHistoryViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            assert result["code"] == 0
            assert result["data"]["count"] == test["expected"]["count"]

    def test_retrieve_latest(self, request_factory):
        gateway = create_gateway()
        stage = G(Stage, api=gateway)
        resource_version = G(ResourceVersion, api=gateway)
        G(ReleaseHistory, api=gateway, created_time=dummy_time.time)
        history = G(
            ReleaseHistory,
            api=gateway,
            stage=stage,
            resource_version=resource_version,
            created_time=dummy_time.time,
        )
        history.stages.add(stage)

        gateway_2 = create_gateway()

        data = [
            {
                "api": gateway,
                "expected": {
                    "stage_names": [stage.name],
                    "created_time": dummy_time.str,
                    "comment": history.comment,
                    "resource_version_name": resource_version.name,
                    "resource_version_title": resource_version.title,
                    "resource_version_comment": resource_version.comment,
                    "resource_version_display": resource_version.object_display,
                    "created_by": history.created_by,
                    "status": history.status,
                    "message": history.message,
                },
            },
            {
                "api": gateway_2,
                "expected": {},
            },
        ]
        for test in data:
            gateway = test["api"]
            request = request_factory.get(f"/apis/{gateway.id}/releases/histories/latest/")

            view = ReleaseHistoryViewSet.as_view({"get": "retrieve_latest"})
            response = view(request, gateway_id=gateway.id)

            result = get_response_json(response)
            assert result["code"] == 0, json.dumps(result)
            assert result["data"] == test["expected"]
