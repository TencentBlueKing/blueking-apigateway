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

from apigateway.apps.esb.component.sync import ComponentSynchronizer

pytestmark = pytest.mark.django_db


class TestComponentSynchronizer:
    def test_get_importing_resources(self, mocker):
        mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentConvertor._get_synchronized_components",
            return_value=[{"id": 1}],
        )
        mock_to_resources = mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentConvertor.to_resources",
            return_value=[{"id": 1, "name": "test", "path": "/test", "method": "GET"}],
        )

        synchronizer = ComponentSynchronizer()
        result = synchronizer.get_importing_resources()

        assert result == [{"id": 1, "name": "test", "path": "/test", "method": "GET"}]
        mock_to_resources.assert_called_once()

    def test_sync_to_resources(self, mocker, fake_gateway, fake_resource, fake_backend, fake_resource_data):
        mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentSynchronizer.get_importing_resources",
            return_value=[{"id": fake_resource.id, "name": "test", "path": "/test", "method": "GET"}],
        )
        mocker.patch(
            "apigateway.apps.esb.component.sync.ResourcesImporter.from_resources",
            return_value=mocker.MagicMock(
                **{
                    "import_resources.return_value": None,
                    "get_deleted_resources.return_value": [],
                    "get_selected_resource_data_list.return_value": [
                        fake_resource_data.copy(update={"resource": fake_resource, "backend": fake_backend}, deep=True)
                    ],
                }
            ),
        )
        mocker.patch(
            "apigateway.apps.esb.component.sync.ComponentResourceBindingHandler.sync",
        )

        synchronizer = ComponentSynchronizer()
        result = synchronizer.sync_to_resources(fake_gateway, "admin")
        assert len(result) == 1
