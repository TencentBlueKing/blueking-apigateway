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

import pytest
from dateutil.tz import tzutc
from django.http import Http404
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.release import serializers
from apigateway.core.models import Gateway, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, create_request, dummy_time


class TestReleaseBatchSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway

    def test_validate_stage_ids(self, mocker):
        stage_1 = G(Stage, api=self.gateway)
        stage_2 = G(Stage, api=self.gateway)

        gateway = G(Gateway)
        stage_3 = G(Stage, api=gateway)

        resource_version = G(ResourceVersion, gateway=self.gateway)

        data = [
            {
                "stage_ids": [stage_1.id, stage_2.id],
                "resource_version_id": resource_version.id,
                "comment": "test",
                "expected": {
                    "gateway": self.gateway,
                    "stage_ids": [stage_1.id, stage_2.id],
                    "resource_version_id": resource_version.id,
                    "comment": "test",
                },
            },
            # error, stage_3 not belong to api
            {
                "stage_ids": [stage_3.id, stage_1.id],
                "resource_version_id": resource_version.id,
                "comment": "test",
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.ReleaseBatchSLZ(data=test, context={"api": self.gateway})
            if test.get("will_error"):
                with pytest.raises(Http404):
                    slz.is_valid()
            else:
                slz.is_valid()
                assert not slz.errors
                assert slz.validated_data == test["expected"]

    def test_validate_resource_version_id(self, mocker):
        gateway = create_gateway()
        resource_version_1 = G(ResourceVersion, gateway=gateway)

        stage = G(Stage, api=self.gateway)
        resource_version_2 = G(ResourceVersion, gateway=self.gateway)

        data = [
            # ok
            {
                "stage_ids": [stage.id],
                "resource_version_id": resource_version_2.id,
                "comment": "test",
                "expected": {
                    "gateway": self.gateway,
                    "stage_ids": [stage.id],
                    "resource_version_id": resource_version_2.id,
                    "comment": "test",
                },
            },
            # error, resoruce_version not belong to self.gateway
            {
                "stage_ids": [stage.id],
                "resource_version_id": resource_version_1.id,
                "comment": "test",
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.ReleaseBatchSLZ(data=test, context={"api": self.gateway})
            if test.get("will_error"):
                with pytest.raises(Http404):
                    slz.is_valid()
            else:
                slz.is_valid()
                assert not slz.errors
                assert slz.validated_data == test["expected"]


class TestReleaseHistoryQuerySLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            {
                "query": "test",
                "stage_id": 12345,
                "created_by": "admin",
                "time_start": 1577263732,
                "time_end": 1577263732,
                "expected": {
                    "query": "test",
                    "stage_id": 12345,
                    "created_by": "admin",
                    "time_start": datetime.datetime(2019, 12, 25, 8, 48, 52, tzinfo=tzutc()),
                    "time_end": datetime.datetime(2019, 12, 25, 8, 48, 52, tzinfo=tzutc()),
                },
            },
            {
                "query": "test",
                "stage_id": 12345,
                "created_by": "admin",
                "time_start": None,
                "time_end": None,
                "expected": {
                    "query": "test",
                    "stage_id": 12345,
                    "created_by": "admin",
                    "time_start": None,
                    "time_end": None,
                },
            },
        ]

        for test in data:
            slz = serializers.ReleaseHistoryQuerySLZ(data=test)
            slz.is_valid()
            self.assertFalse(slz.errors, slz.errors)
            self.assertEqual(slz.validated_data, test["expected"], slz.validated_data)


class TestReleaseHistorySLZ:
    def test_to_representation(self):
        gateway = G(Gateway)
        stage = G(Stage, api=gateway)
        resource_version = G(ResourceVersion, gateway=gateway, name="t1", version="1.0.0", title="测试", comment="test1")
        release_history = G(
            ReleaseHistory,
            gateway=gateway,
            stage=stage,
            resource_version=resource_version,
            created_time=dummy_time.time,
        )
        release_history.stages.add(stage)

        slz = serializers.ReleaseHistorySLZ(instance=release_history)
        assert slz.data == {
            "stage_names": [stage.name],
            "created_time": dummy_time.str,
            "comment": release_history.comment,
            "created_by": release_history.created_by,
            "resource_version_name": resource_version.name,
            "resource_version_title": resource_version.title,
            "resource_version_comment": resource_version.comment,
            "resource_version_display": "1.0.0(测试)",
            "status": release_history.status,
            "message": release_history.message,
        }
