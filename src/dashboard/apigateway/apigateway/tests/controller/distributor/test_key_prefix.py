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
from apigateway.controller.distributor.key_prefix import (
    GatewayKeyPrefixHandler,
    GlobalKeyPrefixHandler,
)


class TestGatewayKeyPrefixHandler:
    """Test GatewayKeyPrefixHandler class"""

    def test_constructor(self):
        """Test GatewayKeyPrefixHandler constructor with various parameters"""
        # Test default values
        handler = GatewayKeyPrefixHandler()
        assert handler.api_version == "v2"
        assert handler.prefix is not None
        assert isinstance(handler.prefix, str)

        # Test custom parameters
        handler = GatewayKeyPrefixHandler(prefix="/custom-prefix", api_version="v3")
        assert handler.prefix == "/custom-prefix"
        assert handler.api_version == "v3"

    def test_get_release_key_prefix(self):
        """Test get_release_key_prefix method with various scenarios"""
        # Test basic functionality
        handler = GatewayKeyPrefixHandler(prefix="/bk-gateway")
        prefix = handler.get_release_key_prefix("test-gateway", "prod")
        assert prefix == "/bk-gateway/v2/gateway/test-gateway/prod/"
        assert prefix.endswith("/")

        # Test with different parameters
        prefix = handler.get_release_key_prefix("my-api", "staging")
        assert prefix == "/bk-gateway/v2/gateway/my-api/staging/"

        # Test with custom api version
        handler = GatewayKeyPrefixHandler(prefix="/bk-gateway", api_version="v3")
        prefix = handler.get_release_key_prefix("test-gateway", "prod")
        assert prefix == "/bk-gateway/v3/gateway/test-gateway/prod/"

        # Test with custom prefix
        handler = GatewayKeyPrefixHandler(prefix="/custom")
        prefix = handler.get_release_key_prefix("api-gateway", "dev")
        assert prefix == "/custom/v2/gateway/api-gateway/dev/"


class TestGlobalKeyPrefixHandler:
    """Test GlobalKeyPrefixHandler class"""

    def test_constructor(self):
        """Test GlobalKeyPrefixHandler constructor with various parameters"""
        # Test default values
        handler = GlobalKeyPrefixHandler()
        assert handler.api_version == "v2"
        assert handler.prefix is not None
        assert isinstance(handler.prefix, str)

        # Test custom parameters
        handler = GlobalKeyPrefixHandler(prefix="/custom-prefix", api_version="v3")
        assert handler.prefix == "/custom-prefix"
        assert handler.api_version == "v3"

    def test_get_release_key_prefix(self):
        """Test get_release_key_prefix method with various scenarios"""
        # Test basic functionality
        handler = GlobalKeyPrefixHandler(prefix="/bk-gateway")
        prefix = handler.get_release_key_prefix()
        assert prefix == "/bk-gateway/v2/global/"
        assert prefix.endswith("/")

        # Test with custom api version
        handler = GlobalKeyPrefixHandler(prefix="/bk-gateway", api_version="v3")
        prefix = handler.get_release_key_prefix()
        assert prefix == "/bk-gateway/v3/global/"

        # Test with custom prefix
        handler = GlobalKeyPrefixHandler(prefix="/custom")
        prefix = handler.get_release_key_prefix()
        assert prefix == "/custom/v2/global/"
