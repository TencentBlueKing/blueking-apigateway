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
from typing import List

from apigateway.apis.open.resource_version import serializers


class TestReleaseInputV1SLZ:
    def _new_slz(self, fake_request, fake_gateway, bk_app_code, stage_names: List[str], resource_version_name: str):
        fake_request.gateway = fake_gateway
        return serializers.ReleaseV1InputSLZ(
            data={
                "resource_version_name": resource_version_name,
                "stage_names": stage_names,
            },
            context={
                "request": fake_request,
            },
        )

    def test_validate(self, mocker, fake_request, fake_gateway):
        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ReleaseV1InputSLZ._get_resource_version_id",
            return_value=None,
        )
        mocker.patch(
            "apigateway.biz.stage.StageHandler.get_stage_ids",
            return_value=None,
        )

        slz = self._new_slz(fake_request, fake_gateway, "test", [], "test")
        slz.is_valid()
        assert not slz.errors

    def test_get_resource_version_id(self, mocker, faker, fake_request, fake_gateway):
        mock_get_by_version = mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ResourceVersion.objects.get_id_by_version",
            return_value=faker.pyint(),
        )
        slz = self._new_slz(fake_request, fake_gateway, "test", [], "test")

        slz._get_resource_version_id(fake_gateway, "1.0.0")
        mock_get_by_version.assert_called_once_with(fake_gateway.id, "1.0.0")
