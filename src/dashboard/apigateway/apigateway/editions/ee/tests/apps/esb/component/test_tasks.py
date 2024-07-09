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

from apigateway.apps.esb.component.exceptions import ComponentReleaseError
from apigateway.apps.esb.bkcore.models import ComponentReleaseHistory
from apigateway.apps.esb.component.tasks import sync_and_release_esb_components
from apigateway.core.models import ResourceVersion

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "updated_resources, release_side_effect",
    [
        (
            [
                {
                    "id": 1,
                    "method": "GET",
                    "path": "/echo/1/",
                    "name": "get_echo_1",
                    "extend_data": {
                        "system_name": "DEMO",
                        "component_id": 100,
                        "component_name": "echo_1",
                        "component_method": "GET",
                        "component_path": "/echo/1/",
                        "component_permission_level": "unlimited",
                    },
                }
            ],
            None,
        ),
        (
            [
                {
                    "id": 1,
                    "method": "GET",
                    "path": "/echo/1/",
                    "name": "get_echo_1",
                    "extend_data": {
                        "system_name": "DEMO",
                        "component_id": 100,
                        "component_name": "echo_1",
                        "component_method": "GET",
                        "component_path": "/echo/1/",
                        "component_permission_level": "unlimited",
                    },
                }
            ],
            ComponentReleaseError("test"),
        ),
    ],
)
def test_sync_and_release_esb_components(mocker, fake_gateway, updated_resources, release_side_effect):
    fake_component_release_history = G(ComponentReleaseHistory, gateway=fake_gateway)
    # not acquired
    mocker.patch(
        "apigateway.apps.esb.component.tasks.get_release_lock",
        return_value=mocker.MagicMock(**{"acquire.return_value": False}),
    )

    sync_and_release_esb_components(fake_gateway.id, fake_component_release_history.id, "admin", False)

    # acquired
    mock_release_lock_release = mocker.MagicMock()
    mocker.patch(
        "apigateway.apps.esb.component.tasks.get_release_lock",
        return_value=mocker.MagicMock(
            **{
                "acquire.return_value": True,
                "release": mock_release_lock_release,
            }
        ),
    )
    mock_sync_to_resources = mocker.patch(
        "apigateway.apps.esb.component.tasks.ComponentSynchronizer.sync_to_resources",
        return_value=updated_resources,
    )
    mock_release = mocker.patch(
        "apigateway.apps.esb.component.tasks.ComponentReleaser.release",
        side_effect=release_side_effect,
    )

    if release_side_effect:
        with pytest.raises(ComponentReleaseError):
            sync_and_release_esb_components(fake_gateway.id, fake_component_release_history.id, "admin", False)
    else:
        sync_and_release_esb_components(fake_gateway.id, fake_component_release_history.id, "admin", False)

    mock_sync_to_resources.asset_called_once_with(fake_gateway, username="admin")
    mock_release.assert_called_once_with()
    mock_release_lock_release.assert_called_once_with()


def test_test_sync_and_release_esb_components_error(mocker, fake_gateway):
    # sync_to_resources 异常时，lock 也会 release
    mock_release_lock_release = mocker.MagicMock()
    mocker.patch(
        "apigateway.apps.esb.component.tasks.get_release_lock",
        return_value=mocker.MagicMock(
            acquire=mocker.MagicMock(return_value=True),
            release=mock_release_lock_release,
        ),
    )

    mocker.patch(
        "apigateway.apps.esb.component.tasks.ComponentSynchronizer.sync_to_resources",
        side_effect=ValueError,
    )

    mock_mark_release_fail = mocker.patch("apigateway.apps.esb.component.tasks.ComponentReleaser.mark_release_fail")

    fake_component_release_history = G(ComponentReleaseHistory, gateway=fake_gateway)
    with pytest.raises(Exception):
        sync_and_release_esb_components(fake_gateway.id, fake_component_release_history.id, "admin", False)

    mock_mark_release_fail.assert_called_once()
    mock_release_lock_release.assert_called_once_with()
