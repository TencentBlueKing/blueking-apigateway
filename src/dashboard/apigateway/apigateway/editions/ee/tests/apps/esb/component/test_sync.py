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
import pytest
from ddf import G

from apigateway.apps.esb.component.sync import ComponentSynchronizer
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestComponentSynchronizer:
    def test_get_importing_resources(self, mocker):
        mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentConvertor._get_synchronized_components",
            return_value=[{"id": 1}],
        )
        mock_to_resources = mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentConvertor.to_resources",
            return_value=[{"id": 1, "method": "GET"}],
        )

        synchronizer = ComponentSynchronizer()
        result = synchronizer.get_importing_resources()

        assert result == [{"id": 1, "method": "GET"}]
        mock_to_resources.assert_called_once()

    def test_sync_to_resources(self, mocker):
        mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentSynchronizer.get_importing_resources",
            return_value=[{"id": 1, "method": "GET"}],
        )
        mock_set_imported_resources = mocker.patch(
            "apigateway.apps.esb.component.sync.ResourcesImporter.set_importing_resources", return_value=None
        )
        mocker.patch("apigateway.apps.esb.component.sync.ResourcesImporter.import_resources", return_value=None)
        mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentResourceBinding.objects.sync",
            return_value=None,
        )

        synchronizer = ComponentSynchronizer()
        result = synchronizer.sync_to_resources(G(Gateway), "admin")
        assert result == [{"id": 1, "method": "GET"}]

        mock_set_imported_resources.assert_called_once_with([{"id": 1, "method": "GET"}])
