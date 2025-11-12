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

from apigateway.controller.convertor.base import GatewayResourceConvertor
from apigateway.controller.convertor.constants import (
    DEFAULT_APISIX_VERSION,
    LABEL_KEY_APISIX_VERSION,
    LABEL_KEY_GATEWAY,
    LABEL_KEY_PUBLISH_ID,
    LABEL_KEY_STAGE,
)


class TestGatewayResourceConvertor:
    """Test GatewayResourceConvertor class"""

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
    def mock_release_data(self, mocker, mock_gateway, mock_stage):
        """Create a mock release data"""
        release_data = mocker.Mock()
        release_data.gateway = mock_gateway
        release_data.stage = mock_stage
        return release_data

    @pytest.fixture
    def convertor(self, mock_release_data):
        """Create a test convertor instance"""

        class TestConvertor(GatewayResourceConvertor):
            def convert(self):
                return []

        return TestConvertor(mock_release_data, publish_id=123)

    def test_gateway_property(self, convertor, mock_gateway):
        """Test gateway property"""
        assert convertor.gateway == mock_gateway

    def test_gateway_id_property(self, convertor):
        """Test gateway_id property"""
        assert convertor.gateway_id == 123

    def test_gateway_name_property(self, convertor):
        """Test gateway_name property"""
        assert convertor.gateway_name == "test-gateway"

    def test_stage_property(self, convertor, mock_stage):
        """Test stage property"""
        assert convertor.stage == mock_stage

    def test_stage_id_property(self, convertor):
        """Test stage_id property"""
        assert convertor.stage_id == 456

    def test_stage_name_property(self, convertor):
        """Test stage_name property"""
        assert convertor.stage_name == "prod"

    def test_get_labels(self, convertor):
        """Test get_gateway_resource_labels method"""
        labels = convertor.get_labels()

        assert labels.get_label(LABEL_KEY_GATEWAY) == "test-gateway"
        assert labels.get_label(LABEL_KEY_STAGE) == "prod"
        assert labels.get_label(LABEL_KEY_PUBLISH_ID) == "123"
        assert labels.get_label(LABEL_KEY_APISIX_VERSION) == DEFAULT_APISIX_VERSION

    def test_get_labels_custom_version(self, mock_release_data):
        """Test get_gateway_resource_labels with custom apisix version"""

        class TestConvertor(GatewayResourceConvertor):
            def convert(self):
                return []

        convertor = TestConvertor(mock_release_data, publish_id=123, apisix_version="3.14")
        labels = convertor.get_labels()

        assert labels.get_label(LABEL_KEY_APISIX_VERSION) == "3.14"

    def test_convertor_initialization_with_default_version(self, mock_release_data):
        """Test convertor initialization with default version"""

        class TestConvertor(GatewayResourceConvertor):
            def convert(self):
                return []

        convertor = TestConvertor(mock_release_data, publish_id=123)
        assert convertor._apisix_version == DEFAULT_APISIX_VERSION

    def test_convertor_initialization_with_custom_version(self, mock_release_data):
        """Test convertor initialization with custom version"""

        class TestConvertor(GatewayResourceConvertor):
            def convert(self):
                return []

        convertor = TestConvertor(mock_release_data, publish_id=123, apisix_version="4.0")
        assert convertor._apisix_version == "4.0"

    def test_convert_method_must_be_implemented(self, mock_release_data):
        """Test that convert method must be implemented"""

        # Should raise error when trying to instantiate without implementing convert
        with pytest.raises(TypeError) as exc_info:

            class IncompleteConvertor(GatewayResourceConvertor):
                pass

            convertor = IncompleteConvertor(mock_release_data, publish_id=123)

        assert "abstract" in str(exc_info.value).lower() or "convert" in str(exc_info.value).lower()
