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
from django_dynamic_fixture import G

from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, dummy_time

pytestmark = pytest.mark.django_db


class TestReleaseBatchCreateApi:
    @pytest.mark.parametrize(
        "configure_hosts,succeeded",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_release_with_hosts(self, request_view, configure_hosts, succeeded, fake_admin_user, mocker, fake_gateway):
        """Test release API with different hosts config of stage objects."""
        mocker.patch(
            "apigateway.biz.releaser.reversion_update_signal.send",
            return_value=None,
        )

        stage_1 = G(Stage, api=fake_gateway, name="prod", status=0)
        stage_2 = G(Stage, api=fake_gateway, name="test", status=0)
        resource_version = G(ResourceVersion, gateway=fake_gateway, _data=json.dumps([]))
        G(Release, gateway=fake_gateway, stage=stage_1, resource_version=resource_version)

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
            "gateway_id": fake_gateway.id,
            "stage_ids": [stage_1.id, stage_2.id],
            "resource_version_id": resource_version.id,
        }

        resp = request_view(
            method="POST",
            view_name="gateway.releases.create",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data=data,
            user=fake_admin_user,
        )

        result = resp.json()

        # There should be one history record for both cases.
        history_qs = ReleaseHistory.objects.filter(stages__id__in=data["stage_ids"]).distinct()
        assert history_qs.count() == 1

        if not succeeded:
            # assert history_qs[0].status == ReleaseStatusEnum.FAILURE.value
            assert resp.status_code != 200, result
        else:
            # The request finished successfully
            # assert history_qs[0].status == ReleaseStatusEnum.SUCCESS.value
            assert resp.status_code == 200, result

            for stage_id in data["stage_ids"]:
                release = Release.objects.get(stage__id=stage_id)
                assert release.resource_version == resource_version


class TestReleaseHistoryListApi:
    def test_list(self, request_view, fake_gateway, request_factory):
        stage_1 = G(Stage, api=fake_gateway, name="test-01")
        stage_2 = G(Stage, api=fake_gateway)

        resource_version = G(ResourceVersion, gateway=fake_gateway)

        history = G(ReleaseHistory, gateway=fake_gateway, stage=stage_1, resource_version=resource_version)
        history.stages.add(stage_1)

        history = G(
            ReleaseHistory, gateway=fake_gateway, stage=stage_2, resource_version=resource_version, created_by="admin"
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
        stage = G(Stage, api=fake_gateway)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        G(ReleaseHistory, gateway=fake_gateway, created_time=dummy_time.time)
        history = G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=stage,
            resource_version=resource_version,
            created_time=dummy_time.time,
        )
        history.stages.add(stage)

        event_1 = G(
            PublishEvent,
            publish=history,
            name=PublishEventNameTypeEnum.ValidateConfiguration.value,
            status=PublishEventStatusTypeEnum.FAILURE.value,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
        )

        gateway_2 = create_gateway()

        data = [
            {
                "gateway": fake_gateway,
                "expected": {
                    "stage_names": [stage.name],
                    "created_time": dummy_time.str,
                    "resource_version_display": resource_version.object_display,
                    "created_by": history.created_by,
                    "source": history.source,
                    "status": f"{event_1.name} {event_1.status}",
                    "cost": (event_1.created_time - history.created_time).total_seconds(),
                    "is_running": False,
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
