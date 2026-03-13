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

from apigateway.apps.data_plane.constants import DEFAULT_DATA_PLANE_NAME, DataPlaneStatusEnum
from apigateway.apps.data_plane.models import DataPlane

pytestmark = pytest.mark.django_db

BK_KRILL_ENCRYPT_SECRET_KEY = "PIMCuSRiVqBg5eSzQqZZrOhGFSUtrlS-8_JlIpjHt0A="


class TestDataPlaneEtcdConfigs:
    """Test DataPlane.etcd_configs property (encrypt/decrypt)"""

    @pytest.fixture(autouse=True)
    def _setup_crypto(self, settings):
        settings.BK_CRYPTO_TYPE = "CLASSIC"
        settings.ENCRYPT_CIPHER_TYPE = "FernetCipher"
        settings.BKKRILL_ENCRYPT_SECRET_KEY = BK_KRILL_ENCRYPT_SECRET_KEY

    def test_encrypt_decrypt_roundtrip(self):
        etcd_config = {"host": "localhost", "port": 2379, "user": "root", "password": "secret"}
        data_plane = G(DataPlane, name="test-roundtrip", _encrypted_etcd_configs="")
        data_plane.etcd_configs = etcd_config
        data_plane.save()

        data_plane.refresh_from_db()
        assert data_plane.etcd_configs == etcd_config

    def test_raises_on_empty(self):
        data_plane = G(DataPlane, name="test-empty", _encrypted_etcd_configs="")
        with pytest.raises(ValueError, match="No etcd_configs"):
            _ = data_plane.etcd_configs

    def test_setter_clears_on_empty_dict(self):
        data_plane = G(DataPlane, name="test-clear", _encrypted_etcd_configs="some_old_value")
        data_plane.etcd_configs = {}
        assert data_plane._encrypted_etcd_configs == ""

    def test_setter_clears_on_none(self):
        data_plane = G(DataPlane, name="test-clear-none", _encrypted_etcd_configs="some_old_value")
        data_plane.etcd_configs = None
        assert data_plane._encrypted_etcd_configs == ""

    def test_raises_on_corrupt_data(self):
        data_plane = G(DataPlane, name="test-corrupt", _encrypted_etcd_configs="not_valid_encrypted_data")
        with pytest.raises(ValueError, match="Failed to decrypt"):
            _ = data_plane.etcd_configs


class TestDataPlaneIsActive:
    def test_active(self):
        data_plane = G(DataPlane, name="test-active", status=DataPlaneStatusEnum.ACTIVE.value)
        assert data_plane.is_active is True

    def test_inactive(self):
        data_plane = G(DataPlane, name="test-inactive", status=DataPlaneStatusEnum.INACTIVE.value)
        assert data_plane.is_active is False


class TestDataPlaneIsDefault:
    def test_default(self):
        data_plane = G(DataPlane, name=DEFAULT_DATA_PLANE_NAME)
        assert data_plane.is_default() is True

    def test_non_default(self):
        data_plane = G(DataPlane, name="non-default")
        assert data_plane.is_default() is False


class TestDataPlaneManager:
    def test_get_default_exists(self):
        dp = G(DataPlane, name=DEFAULT_DATA_PLANE_NAME)
        result = DataPlane.objects.get_default()
        assert result.id == dp.id

    def test_get_default_not_exists(self):
        with pytest.raises(DataPlane.DoesNotExist):
            DataPlane.objects.get_default()

    def test_get_recommended_with_recommended_plane(self):
        G(DataPlane, name="recommended", is_recommend=True, status=DataPlaneStatusEnum.ACTIVE.value)
        G(DataPlane, name=DEFAULT_DATA_PLANE_NAME, is_recommend=False, status=DataPlaneStatusEnum.ACTIVE.value)

        result = DataPlane.objects.get_recommended()
        assert result is not None
        assert result.name == "recommended"

    def test_get_recommended_falls_back_to_default(self):
        G(DataPlane, name=DEFAULT_DATA_PLANE_NAME, is_recommend=False, status=DataPlaneStatusEnum.ACTIVE.value)

        result = DataPlane.objects.get_recommended()
        assert result is not None
        assert result.name == DEFAULT_DATA_PLANE_NAME

    def test_get_recommended_skips_inactive(self):
        G(DataPlane, name="recommended-inactive", is_recommend=True, status=DataPlaneStatusEnum.INACTIVE.value)
        default = G(DataPlane, name=DEFAULT_DATA_PLANE_NAME, status=DataPlaneStatusEnum.ACTIVE.value)

        result = DataPlane.objects.get_recommended()
        assert result is not None
        assert result.id == default.id

    def test_get_active_data_planes(self):
        G(DataPlane, name="active1", status=DataPlaneStatusEnum.ACTIVE.value)
        G(DataPlane, name="active2", status=DataPlaneStatusEnum.ACTIVE.value)
        G(DataPlane, name="inactive1", status=DataPlaneStatusEnum.INACTIVE.value)

        result = DataPlane.objects.get_active_data_planes()
        names = {dp.name for dp in result}
        assert "active1" in names
        assert "active2" in names
        assert "inactive1" not in names
