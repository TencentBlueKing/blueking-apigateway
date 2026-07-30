#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from unittest.mock import Mock

from apigateway.controller.tasks.release import update_release_data_after_success
from apigateway.core.constants import ReleaseHistoryStatusEnum


def test_update_release_success_reconciles_without_reversing_publish_on_failure(mocker):
    latest_event = Mock()
    latest_event.get_release_history_status.return_value = ReleaseHistoryStatusEnum.SUCCESS.value
    mocker.patch(
        "apigateway.controller.tasks.release.PublishEvent.objects.get_release_history_id_to_latest_publish_event_map",
        return_value={1: latest_event},
    )
    gateway = Mock(id=10)
    stage = Mock(id=20)
    release = Mock(id=30, gateway=gateway, gateway_id=10, stage=stage)
    resource_version = Mock(id=40)
    mocker.patch("apigateway.controller.tasks.release.Release.objects.get", return_value=release)
    mocker.patch(
        "apigateway.controller.tasks.release.ResourceVersion.objects.get",
        return_value=resource_version,
    )
    mocker.patch("apigateway.controller.tasks.release.Stage.objects.filter")
    mocker.patch("apigateway.controller.tasks.release.ReleasedResource.objects")
    mocker.patch("apigateway.controller.tasks.release.clear_unreleased_resource")
    mocker.patch(
        "apigateway.controller.tasks.release.ResourceDocVersion.objects.get_by_resource_version_id",
        return_value=Mock(),
    )
    mocker.patch("apigateway.controller.tasks.release.ReleasedResourceDoc.objects")
    mocker.patch("apigateway.controller.tasks.release.clear_unreleased_resource_doc")
    mocker.patch("apigateway.controller.tasks.release.update_stage_mcp_server_related_resource_names")
    reconcile = mocker.patch(
        "apigateway.controller.tasks.release.OAuth2BuiltinPermissionReconciler"
    ).return_value.reconcile_gateway
    reconcile.side_effect = RuntimeError("redis unavailable")

    update_release_data_after_success(
        publish_id=1,
        release_id=30,
        resource_version_id=40,
        author="admin",
        comment="",
    )

    reconcile.assert_called_once_with(gateway)
