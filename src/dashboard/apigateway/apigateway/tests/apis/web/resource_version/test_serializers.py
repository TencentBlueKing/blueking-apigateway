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
import arrow
import pytest
from django_dynamic_fixture import G
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.resource_version import serializers
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.tests.utils.testing import dummy_time
from apigateway.utils import time as time_utils


class TestResourceVersionInfoSLZ:
    def test_validate_version_unique(self, fake_gateway):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")

        with pytest.raises(ValidationError):
            slz = serializers.ResourceVersionInfoSLZ()
            slz._validate_version_unique(fake_gateway, "1.0.0")

        # same instance
        slz = serializers.ResourceVersionInfoSLZ(instance=resource_version)
        assert slz._validate_version_unique(fake_gateway, "1.0.0") is None

        # version not exist
        slz = serializers.ResourceVersionInfoSLZ()
        assert slz._validate_version_unique(fake_gateway, "1.0.1") is None

    def test_create(self, mocker, fake_gateway):
        mocker.patch(
            "apigateway.apis.web.resource_version.serializers.time_utils.now_datetime",
            return_value=dummy_time.time,
        )
        mocker.patch(
            "apigateway.apis.web.resource_version.serializers.ResourceVersionInfoSLZ._validate_resource_count",
            return_value=None,
        )
        slz = serializers.ResourceVersionInfoSLZ(
            data={
                "version": "1.0.2",
                "title": "test",
                "comment": "",
            },
            context={
                "api": fake_gateway,
            },
        )
        slz.is_valid()
        assert not slz.errors

        instance = slz.save(data=[])
        time_str = time_utils.format(dummy_time.time, fmt="YYYYMMDDHHmmss")
        assert instance.name.startswith(f"{fake_gateway.name}_{time_str}_")
        assert instance.version == "1.0.2"


class TestResourceVersionListOutputSLZ:
    def test_to_representation(self):
        gateway = G(Gateway)
        resource_version = G(
            ResourceVersion,
            gateway=gateway,
            version="1.0.1",
            title="test",
            created_time=arrow.get("2019-01-01 12:30:00").datetime,
        )

        queryset = ResourceVersion.objects.filter(gateway=gateway).values(
            "id", "version", "name", "title", "comment", "created_time"
        )

        slz = serializers.ResourceVersionListOutputSLZ(
            instance=queryset,
            many=True,
            context={
                "released_stages": {
                    resource_version.id: [
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
                "resource_version_ids_has_sdk": [],
            },
        )
        assert slz.data == [
            {
                "id": resource_version.id,
                "version": resource_version.version,
                "name": resource_version.name,
                "title": resource_version.title,
                "comment": resource_version.comment,
                "resource_version_display": "1.0.1(test)",
                "has_sdk": False,
                "released_stages": [
                    {
                        "id": 1,
                        "name": "prod",
                    },
                    {
                        "id": 2,
                        "name": "test",
                    },
                ],
                "created_time": "2019-01-01 20:30:00",
            },
        ]
