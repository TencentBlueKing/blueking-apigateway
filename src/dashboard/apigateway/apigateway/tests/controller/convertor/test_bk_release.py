#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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

from apigateway.controller.convertor import BkReleaseConvertor
from apigateway.controller.convertor.constants import (
    DEFAULT_APISIX_VERSION,
    LABEL_KEY_APISIX_VERSION,
    LABEL_KEY_GATEWAY,
    LABEL_KEY_PUBLISH_ID,
    LABEL_KEY_STAGE,
)
from apigateway.controller.models import BkRelease


class TestBkReleaseConvertor:
    """Test BkReleaseConvertor class"""

    @pytest.fixture
    def mock_gateway(self, mocker):
        """Create a mock gateway"""
        gateway = mocker.Mock()
        gateway.pk = 123
        gateway.name = "test-gateway"
        return gateway

    @pytest.fixture
    def mock_stage(self, mocker):
        """Create a mock stage"""
        stage = mocker.Mock()
        stage.pk = 456
        stage.name = "prod"
        return stage

    @pytest.fixture
    def mock_resource_version(self, mocker):
        """Create a mock resource version"""
        resource_version = mocker.Mock()
        resource_version.version = "v1.0.0"
        return resource_version

    @pytest.fixture
    def mock_release_data(self, mocker, mock_gateway, mock_stage, mock_resource_version):
        """Create a mock release data"""
        release_data = mocker.Mock()
        release_data.gateway = mock_gateway
        release_data.stage = mock_stage
        release_data.resource_version = mock_resource_version
        return release_data

    @pytest.fixture
    def convertor(self, mock_release_data):
        """Create a BkReleaseConvertor instance"""
        return BkReleaseConvertor(release_data=mock_release_data, publish_id=789)

    def test_convert_returns_correct_bk_release(self, convertor, mocker):
        """Test that convert method returns correct BkRelease model with all fields"""
        mock_time = "2021-01-01 00:00:00"
        mocker.patch("apigateway.controller.convertor.bk_release.now_str", return_value=mock_time)

        result = convertor.convert()

        # Test return type and structure
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BkRelease)

        bk_release = result[0]

        # Test all fields
        assert bk_release.id == "bk.release.test-gateway.prod"
        assert bk_release.publish_id == 789
        assert bk_release.publish_time == mock_time
        assert bk_release.resource_version == "v1.0.0"
        assert bk_release.kind == "_bk_release"
        assert bk_release.apisix_version == DEFAULT_APISIX_VERSION

        # Test labels
        labels = bk_release.labels
        assert labels is not None
        assert labels.get_label(LABEL_KEY_GATEWAY) == "test-gateway"
        assert labels.get_label(LABEL_KEY_STAGE) == "prod"
        assert labels.get_label(LABEL_KEY_PUBLISH_ID) == "789"
        assert labels.get_label(LABEL_KEY_APISIX_VERSION) is not None

    def test_convert_with_different_gateway_and_stage(self, mocker):
        """Test convert with different gateway and stage names"""
        # Create mocks with different names
        gateway = mocker.Mock()
        gateway.pk = 999
        gateway.name = "my-api-gateway"

        stage = mocker.Mock()
        stage.pk = 888
        stage.name = "staging"

        resource_version = mocker.Mock()
        resource_version.version = "v2.1.0"

        release_data = mocker.Mock()
        release_data.gateway = gateway
        release_data.stage = stage
        release_data.resource_version = resource_version

        convertor = BkReleaseConvertor(release_data=release_data, publish_id=555)
        result = convertor.convert()
        bk_release = result[0]

        assert bk_release.id == "bk.release.my-api-gateway.staging"
        assert bk_release.publish_id == 555
        assert bk_release.resource_version == "v2.1.0"
