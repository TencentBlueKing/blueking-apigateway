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
from django_dynamic_fixture import G

from apigateway.apis.web.resource_version import serializers
from apigateway.core.models import Gateway, ResourceVersion


class TestResourceVersionInfoSLZ:
    def test_create(self, fake_gateway, fake_resource):
        slz = serializers.ResourceVersionCreateInputSLZ(
            data={
                "version": "1.0.2",
                "comment": "",
            },
            context={
                "gateway": fake_gateway,
            },
        )
        slz.is_valid()
        assert not slz.errors


class TestResourceVersionListOutputSLZ:
    def test_to_representation(self):
        gateway = G(Gateway)
        resource_version = G(
            ResourceVersion,
            gateway=gateway,
            version="1.0.1",
            created_time=arrow.get("2019-01-01 12:30:00").datetime,
        )

        queryset = ResourceVersion.objects.filter(gateway=gateway).values("id", "version", "comment", "created_time")

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
                "resource_version_ids_sdk_count": {},
            },
        )
        assert slz.data == [
            {
                "id": resource_version.id,
                "version": resource_version.version,
                "comment": resource_version.comment,
                "resource_version_display": "1.0.1",
                "sdk_count": 0,
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
