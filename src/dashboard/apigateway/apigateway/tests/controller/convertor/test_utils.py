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

from apigateway.controller.convertor.utils import UrlInfo, truncate_string


class TestTruncateString:
    """Test truncate_string function"""

    def test_truncate_string_shorter_than_max(self):
        """Test truncate string when value is shorter than max length"""
        result = truncate_string("hello", 10)
        assert result == "hello"

    def test_truncate_string_equal_to_max(self):
        """Test truncate string when value equals max length"""
        result = truncate_string("hello", 5)
        assert result == "hello"

    def test_truncate_string_longer_than_max(self):
        """Test truncate string when value is longer than max length"""
        result = truncate_string("hello world", 8)
        assert result == "hello..."
        assert len(result) == 8

    def test_truncate_string_with_ellipsis(self):
        """Test truncate string adds ellipsis correctly"""
        result = truncate_string("this is a long string", 10)
        assert result.endswith("...")
        assert len(result) == 10

    def test_truncate_string_empty(self):
        """Test truncate string with empty string"""
        result = truncate_string("", 10)
        assert result == ""

    def test_truncate_string_exactly_at_boundary(self):
        """Test truncate string at exact boundary"""
        value = "x" * 20
        result = truncate_string(value, 20)
        assert result == value
        assert len(result) == 20

    def test_truncate_string_one_over_boundary(self):
        """Test truncate string one character over boundary"""
        value = "x" * 11
        result = truncate_string(value, 10)
        assert result == "xxxxxxx..."
        assert len(result) == 10


class TestUrlInfo:
    """Test UrlInfo class"""

    def test_url_info_http(self):
        """Test UrlInfo with HTTP URL"""
        url_info = UrlInfo("http://example.com/path")
        assert url_info.scheme == "http"
        assert url_info.domain == "example.com"
        assert url_info.port == 80  # Default HTTP port
        assert url_info.path == "/path"

    def test_url_info_https(self):
        """Test UrlInfo with HTTPS URL"""
        url_info = UrlInfo("https://example.com/path")
        assert url_info.scheme == "https"
        assert url_info.domain == "example.com"
        assert url_info.port == 443  # Default HTTPS port
        assert url_info.path == "/path"

    def test_url_info_with_explicit_port(self):
        """Test UrlInfo with explicit port"""
        url_info = UrlInfo("http://example.com:8080/path")
        assert url_info.scheme == "http"
        assert url_info.domain == "example.com"
        assert url_info.port == 8080
        assert url_info.path == "/path"

    def test_url_info_with_query(self):
        """Test UrlInfo with query string"""
        url_info = UrlInfo("http://example.com/path?key=value&foo=bar")
        assert url_info.scheme == "http"
        assert url_info.domain == "example.com"
        assert url_info.path == "/path"
        assert url_info.query == "key=value&foo=bar"

    def test_url_info_without_path(self):
        """Test UrlInfo without path"""
        url_info = UrlInfo("http://example.com")
        assert url_info.scheme == "http"
        assert url_info.domain == "example.com"
        assert url_info.port == 80
        assert url_info.path == ""

    def test_url_info_with_complex_path(self):
        """Test UrlInfo with complex path"""
        url_info = UrlInfo("http://example.com/api/v1/users/123")
        assert url_info.path == "/api/v1/users/123"

    def test_url_info_custom_port_https(self):
        """Test UrlInfo with custom port on HTTPS"""
        url_info = UrlInfo("https://example.com:8443/secure")
        assert url_info.scheme == "https"
        assert url_info.port == 8443
        assert url_info.path == "/secure"

    def test_url_info_netloc(self):
        """Test UrlInfo netloc attribute"""
        url_info = UrlInfo("http://example.com:8080")
        assert url_info.netloc == "example.com:8080"

        url_info2 = UrlInfo("http://example.com")
        assert url_info2.netloc == "example.com"

    def test_url_info_unknown_scheme(self):
        """Test UrlInfo with unknown scheme"""
        url_info = UrlInfo("grpc://example.com/service")
        assert url_info.scheme == "grpc"
        assert url_info.domain == "example.com"
        assert url_info.port is None  # No default port for grpc

    def test_url_info_localhost(self):
        """Test UrlInfo with localhost"""
        url_info = UrlInfo("http://localhost:3000/api")
        assert url_info.domain == "localhost"
        assert url_info.port == 3000
        assert url_info.path == "/api"

    def test_url_info_ip_address(self):
        """Test UrlInfo with IP address"""
        url_info = UrlInfo("http://192.168.1.1:8080/api")
        assert url_info.domain == "192.168.1.1"
        assert url_info.port == 8080

    def test_url_info_default_ports(self):
        """Test UrlInfo default ports mapping"""
        assert UrlInfo._default_ports["http"] == 80
        assert UrlInfo._default_ports["https"] == 443

    def test_url_info_with_subdomain(self):
        """Test UrlInfo with subdomain"""
        url_info = UrlInfo("https://api.example.com/v1/users")
        assert url_info.domain == "api.example.com"
        assert url_info.path == "/v1/users"

    def test_url_info_empty_query(self):
        """Test UrlInfo with empty query"""
        url_info = UrlInfo("http://example.com/path")
        assert url_info.query == ""
