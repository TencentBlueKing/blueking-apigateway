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

import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.open.resource_version import serializers


class TestReleaseV1SLZ:
    def _new_slz(self, fake_request, fake_gateway, bk_app_code, stage_names: List[str], resource_version_name: str):
        fake_request.gateway = fake_gateway
        return serializers.ReleaseV1SLZ(
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
            "apigateway.apis.open.resource_version.serializers.ReleaseV1SLZ._get_resource_version_id",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ReleaseV1SLZ._get_stage_ids",
            return_value=None,
        )

        slz = self._new_slz(fake_request, fake_gateway, "test", [], "test")
        slz.is_valid()
        assert not slz.errors

    def test_get_resource_version_id(self, mocker, faker, fake_request, fake_gateway):
        mock_get_by_version = mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ReleaseV1SLZ._get_resource_version_id_by_version",
            return_value=faker.pyint(),
        )
        mock_get_by_name = mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ReleaseV1SLZ._get_resource_version_id_by_name",
            return_value=faker.pyint(),
        )
        slz = self._new_slz(fake_request, fake_gateway, "test", [], "test")

        slz._get_resource_version_id(fake_gateway, None, "test")
        mock_get_by_version.assert_not_called()
        mock_get_by_name.assert_called_once_with(fake_gateway, "test")

        mock_get_by_name.reset_mock()
        slz._get_resource_version_id(fake_gateway, "1.0.0", "test")
        mock_get_by_version.assert_called_once_with(fake_gateway, "1.0.0")
        mock_get_by_name.assert_not_called()

    def test_get_resource_version_id_by_name(self, mocker, faker, fake_gateway):
        slz = serializers.ReleaseV1SLZ()

        id_ = faker.pyint(min_value=1)
        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ResourceVersion.objects.get_id_by_name",
            return_value=id_,
        )
        assert slz._get_resource_version_id_by_name(fake_gateway, faker.pystr()) == id_

        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ResourceVersion.objects.get_id_by_name",
            return_value=None,
        )
        with pytest.raises(ValidationError):
            slz._get_resource_version_id_by_name(fake_gateway, faker.pystr())

    def test_get_resource_version_id_by_version(self, mocker, faker, fake_gateway):
        slz = serializers.ReleaseV1SLZ()

        id_ = faker.pyint(min_value=1)
        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ResourceVersion.objects.get_id_by_version",
            return_value=id_,
        )
        assert slz._get_resource_version_id_by_version(fake_gateway, faker.pystr()) == id_

        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ResourceVersion.objects.get_id_by_version",
            return_value=None,
        )
        with pytest.raises(ValidationError):
            slz._get_resource_version_id_by_version(fake_gateway, faker.pystr())

    @pytest.mark.parametrize(
        "stage_names, expected, will_error",
        [
            ([], [1, 2], False),
            (["prod"], [1], False),
            (["stag"], None, True),
        ],
    )
    def test_get_stage_ids(self, mocker, fake_request, fake_gateway, stage_names, expected, will_error):
        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.Stage.objects.get_name_id_map",
            return_value={"prod": 1, "test": 2},
        )

        slz = self._new_slz(fake_request, fake_gateway, "test", stage_names, "test")

        if will_error:
            with pytest.raises(Exception):
                slz._get_stage_ids(fake_gateway, stage_names)
            return

        result = slz._get_stage_ids(fake_gateway, stage_names)
        assert expected == sorted(result)
