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
from apigateway.controller.convertor.proto import ProtoConvertor


class TestProtoConvertor:
    """Test ProtoConvertor class"""

    @pytest.fixture
    def mock_release_data(self, mocker):
        """Create a mock release data"""
        release_data = mocker.Mock()
        release_data.gateway = mocker.Mock()
        release_data.gateway.pk = 123
        release_data.gateway.name = "test-gateway"
        release_data.stage = mocker.Mock()
        release_data.stage.pk = 456
        release_data.stage.name = "prod"
        return release_data

    def test_proto_convertor_initialization(self, mock_release_data):
        """Test ProtoConvertor initialization"""
        convertor = ProtoConvertor(mock_release_data)
        assert convertor is not None
        assert convertor._release_data == mock_release_data

    def test_convert_not_implemented(self, mock_release_data):
        """Test that convert method raises NotImplementedError"""
        convertor = ProtoConvertor(mock_release_data)

        with pytest.raises(NotImplementedError):
            convertor.convert()

    def test_proto_convertor_is_gateway_resource_convertor(self, mock_release_data):
        """Test that ProtoConvertor is a GatewayResourceConvertor"""
        convertor = ProtoConvertor(mock_release_data)
        assert isinstance(convertor, GatewayResourceConvertor)

    def test_proto_convertor_inherits_gateway_properties(self, mock_release_data):
        """Test that ProtoConvertor inherits properties from GatewayResourceConvertor"""
        convertor = ProtoConvertor(mock_release_data)

        # Test inherited properties
        assert convertor.gateway_id == 123
        assert convertor.gateway_name == "test-gateway"
        assert convertor.stage_id == 456
        assert convertor.stage_name == "prod"

    def test_proto_convertor_with_custom_apisix_version(self, mock_release_data):
        """Test ProtoConvertor with custom apisix version"""
        convertor = ProtoConvertor(mock_release_data, apisix_version="3.14")
        assert convertor._apisix_version == "3.14"
