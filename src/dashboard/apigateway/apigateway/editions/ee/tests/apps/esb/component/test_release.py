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

from apigateway.apps.esb.bkcore.models import ComponentReleaseHistory
from apigateway.apps.esb.component.release import ComponentReleaser
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import ResourceVersion

pytestmark = pytest.mark.django_db


class TestComponentReleaser:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_gateway):
        self.releaser = ComponentReleaser(fake_gateway, "admin")

    def test_create_resource_version(self, mocker):
        mock_create_resource_version = mocker.patch(
            "apigateway.apps.esb.component.release.ResourceVersionHandler.create_resource_version",
            return_value=mocker.MagicMock(id=10),
        )

        self.releaser.create_release_history()
        self.releaser.create_resource_version()

        mock_create_resource_version.assert_called_once_with(
            self.releaser.gateway,
            data={
                "version": f"1.0.{self.releaser.release_history.id}",
                "title": f"1.0.{self.releaser.release_history.id}",
                "comment": "同步组件到 API 网关",
            },
            username="admin",
        )

    def test_mark_release_fail(self, mocker):
        self.releaser.create_release_history()

        self.releaser.mark_release_fail("error")

        release_history = ComponentReleaseHistory.objects.get(id=self.releaser.release_history.id)
        assert release_history.status == ReleaseStatusEnum.FAILURE.value
        assert release_history.message == "error"

    def test_mark_release_success(self):
        self.releaser.create_release_history()

        self.releaser.mark_release_success()

        release_history = ComponentReleaseHistory.objects.get(id=self.releaser.release_history.id)
        assert release_history.status == ReleaseStatusEnum.SUCCESS.value

    def test_prepare_version(self, mocker, fake_gateway):
        result = self.releaser._prepare_version(fake_gateway.id, 3)
        assert result == "1.0.3"

        mocker.patch(
            "apigateway.apps.esb.component.release.ResourceVersion.objects.check_version_exists",
            return_value=True,
        )

        result = self.releaser._prepare_version(fake_gateway.id, 3)
        assert result.startswith("1.0.3+")

    def test_get_resource_version_id(self):
        assert self.releaser._get_resource_version_id() == 0

        self.releaser.resource_version = G(ResourceVersion, gateway=self.releaser.gateway)
        assert self.releaser._get_resource_version_id() > 0
