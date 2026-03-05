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
import pytest
from ddf import G
from rest_framework.exceptions import ValidationError

from apigateway.apps.data_plane.constants import DEFAULT_DATA_PLANE_NAME, DataPlaneStatusEnum
from apigateway.apps.data_plane.models import DataPlane
from apigateway.biz.data_plane.data_plane import (
    _get_default_data_plane_id,
    _get_te_bp_sync_data_plane_ids,
    _resolve_data_plane_ids_by_names,
    get_sync_data_plane_ids,
)

pytestmark = pytest.mark.django_db


class TestResolveDataPlaneIdsByNames:
    def test_success(self):
        dp1 = G(DataPlane, name="plane-a", status=DataPlaneStatusEnum.ACTIVE.value)
        dp2 = G(DataPlane, name="plane-b", status=DataPlaneStatusEnum.ACTIVE.value)

        result = _resolve_data_plane_ids_by_names(["plane-a", "plane-b"])
        assert set(result) == {dp1.id, dp2.id}

    def test_missing_raises_validation_error(self):
        G(DataPlane, name="exists", status=DataPlaneStatusEnum.ACTIVE.value)

        with pytest.raises(ValidationError):
            _resolve_data_plane_ids_by_names(["exists", "does-not-exist"])

    def test_deduplicates(self):
        dp = G(DataPlane, name="dup-plane", status=DataPlaneStatusEnum.ACTIVE.value)

        result = _resolve_data_plane_ids_by_names(["dup-plane", "dup-plane"])
        assert result == [dp.id]


class TestGetDefaultDataPlaneId:
    def test_success(self):
        dp = G(DataPlane, name=DEFAULT_DATA_PLANE_NAME, status=DataPlaneStatusEnum.ACTIVE.value)
        assert _get_default_data_plane_id() == dp.id

    def test_not_found_raises(self):
        with pytest.raises(ValueError, match="Default data plane not found"):
            _get_default_data_plane_id()


class TestGetTeBpSyncDataPlaneIds:
    @pytest.fixture()
    def bp_data_plane(self, settings):
        settings.BK_PLUGINS_DATA_PLANE_NAME = "bk-plugins"
        return G(DataPlane, name="bk-plugins", status=DataPlaneStatusEnum.ACTIVE.value)

    def test_not_start_returns_default(self, settings, bp_data_plane):
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = "not_start"
        default_id = 999

        result = _get_te_bp_sync_data_plane_ids(default_id)
        assert result == [default_id]

    def test_start_returns_both(self, settings, bp_data_plane):
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = "start"
        default_id = 999

        result = _get_te_bp_sync_data_plane_ids(default_id)
        assert set(result) == {default_id, bp_data_plane.id}

    def test_done_returns_bp_only(self, settings, bp_data_plane):
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = "done"
        default_id = 999

        result = _get_te_bp_sync_data_plane_ids(default_id)
        assert result == [bp_data_plane.id]

    def test_bp_plane_not_found_falls_back_to_default(self, settings):
        settings.BK_PLUGINS_DATA_PLANE_NAME = "nonexistent-bp"
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = "done"
        default_id = 999

        result = _get_te_bp_sync_data_plane_ids(default_id)
        assert result == [default_id]


class TestGetSyncDataPlaneIds:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.default_dp = G(DataPlane, name=DEFAULT_DATA_PLANE_NAME, status=DataPlaneStatusEnum.ACTIVE.value)

    def test_with_explicit_names(self):
        dp = G(DataPlane, name="explicit-plane", status=DataPlaneStatusEnum.ACTIVE.value)
        result = get_sync_data_plane_ids("any-gateway", data_plane_names=["explicit-plane"])
        assert result == [dp.id]

    def test_default_fallback(self, settings):
        settings.EDITION = "ee"
        result = get_sync_data_plane_ids("my-gateway")
        assert result == [self.default_dp.id]

    def test_te_plugin_gateway_routing(self, settings):
        settings.EDITION = "te"
        settings.BK_PLUGINS_DATA_PLANE_NAME = "bk-plugins"
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = "not_start"

        result = get_sync_data_plane_ids("bp-my-plugin")
        assert result == [self.default_dp.id]

    def test_te_non_plugin_gateway_uses_default(self, settings):
        settings.EDITION = "te"
        result = get_sync_data_plane_ids("regular-gateway")
        assert result == [self.default_dp.id]
