#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.controller.tasks.syncing import distribute_global_resources


class TestDistributeGlobalResources:
    def test_should_distribute_to_all_active_data_planes(self, mocker):
        data_plane_1 = mocker.Mock(id=1, name="dp-1")
        data_plane_2 = mocker.Mock(id=2, name="dp-2")
        mocker.patch(
            "apigateway.controller.tasks.syncing.DataPlane.objects.get_active_data_planes",
            return_value=[data_plane_1, data_plane_2],
        )

        distributor_1 = mocker.Mock()
        distributor_1.distribute.return_value = (True, "ok")
        distributor_2 = mocker.Mock()
        distributor_2.distribute.return_value = (True, "ok")
        distributor_cls = mocker.patch(
            "apigateway.controller.tasks.syncing.GlobalResourceDistributor",
            side_effect=[distributor_1, distributor_2],
        )

        result = distribute_global_resources()

        assert result is True
        assert distributor_cls.call_count == 2
        distributor_cls.assert_any_call(data_plane=data_plane_1)
        distributor_cls.assert_any_call(data_plane=data_plane_2)
        distributor_1.distribute.assert_called_once()
        distributor_2.distribute.assert_called_once()

    def test_should_continue_when_one_data_plane_fails(self, mocker):
        data_plane_1 = mocker.Mock(id=1, name="dp-1")
        data_plane_2 = mocker.Mock(id=2, name="dp-2")
        mocker.patch(
            "apigateway.controller.tasks.syncing.DataPlane.objects.get_active_data_planes",
            return_value=[data_plane_1, data_plane_2],
        )

        distributor_1 = mocker.Mock()
        distributor_1.distribute.return_value = (False, "boom")
        distributor_2 = mocker.Mock()
        distributor_2.distribute.return_value = (True, "ok")
        distributor_cls = mocker.patch(
            "apigateway.controller.tasks.syncing.GlobalResourceDistributor",
            side_effect=[distributor_1, distributor_2],
        )

        result = distribute_global_resources()

        assert result is False
        assert distributor_cls.call_count == 2
        distributor_1.distribute.assert_called_once()
        distributor_2.distribute.assert_called_once()

    def test_should_return_false_when_no_active_data_plane(self, mocker):
        mocker.patch(
            "apigateway.controller.tasks.syncing.DataPlane.objects.get_active_data_planes",
            return_value=[],
        )
        distributor_cls = mocker.patch("apigateway.controller.tasks.syncing.GlobalResourceDistributor")

        result = distribute_global_resources()

        assert result is False
        distributor_cls.assert_not_called()
