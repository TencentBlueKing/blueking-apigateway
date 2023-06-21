import re

import pytest


class TestBkCorsPluginForm:
    allow_origins_pattern = (
        "^(|\\*|\\*\\*|null|http(s)?://[-a-zA-Z0-9:\\[\\]\\.]+(,http(s)?://[-a-zA-Z0-9:\\[\\]\\.]+)*)$"
    )

    allow_origins_by_regex_pattern = "^(\\^)?[-a-zA-Z0-9:/\\[\\]\\{\\}\\(\\)\\.\\*\\+\\?\\|\\\\]+(\\$)?$"

    allow_methods_pattern = (
        "^(\\*|\\*\\*|(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)"
        "(,(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE))*)$"
    )

    allow_headers_pattern = "^(\\*|\\*\\*|[-a-zA-Z0-9]+(,[-a-zA-Z0-9]+)*)$"

    expose_headers_pattern = "^(|\\*|\\*\\*|[-a-zA-Z0-9]+(,[-a-zA-Z0-9]+)*)$"

    @pytest.mark.parametrize(
        "allow_origins",
        [
            "",
            "*",
            "**",
            "null",
            "http://example.com",
            "https://example.com",
            "http://example.com:8080",
            "http://example.com:8080,http://foo.com:8000",
            "http://[1:1::1]:8080",
        ],
    )
    def test_allow_origins_pattern(self, allow_origins):
        assert re.match(self.allow_origins_pattern, allow_origins)

    @pytest.mark.parametrize(
        "allow_origins",
        [
            "test",
            "http://foo.com/",
            "http://foo.com:8080,",
            "http://foo.com,test",
            "http://foo.com,",
            "http://foo.com, http://example.com",
        ],
    )
    def test_allow_origins_pattern__error(self, allow_origins):
        assert not re.match(self.allow_origins_pattern, allow_origins)

    @pytest.mark.parametrize(
        "allow_origins_by_regex",
        [
            "http://foo.com",
            "http://.*.foo.com",
            "http://foo.com:8080",
            "^http://.*\\.foo\\.com:8000$",
            "^https://.*\\.foo\\.com$",
            "http://[1:1::1]:8000",
            "^http(s)?://.*\\.example\\.com$",
            "^http(s)?://.*\\.(foo|example)\\.com$",
            "http://.+\\.foo\\.com",
        ],
    )
    def test_allow_origins_by_regex(self, allow_origins_by_regex):
        assert re.match(self.allow_origins_by_regex_pattern, allow_origins_by_regex)

    @pytest.mark.parametrize(
        "allow_origins_by_regex",
        [
            "",
            " ",
            "http://foo.com,",
        ],
    )
    def test_allow_origins_by_regex__error(self, allow_origins_by_regex):
        assert not re.match(self.allow_origins_by_regex_pattern, allow_origins_by_regex)

    @pytest.mark.parametrize(
        "allow_methods",
        [
            "*",
            "**",
            "GET",
            "GET,POST,PUT,DELETE,PATCH,HEAD,OPTIONS,CONNECT,TRACE",
            "GET,POST",
        ],
    )
    def test_allow_methods(self, allow_methods):
        assert re.match(self.allow_methods_pattern, allow_methods)

    @pytest.mark.parametrize(
        "allow_methods",
        [
            "",
            "GET,",
            "GET,POST,",
            "GET, POST",
        ],
    )
    def test_allow_methods__error(self, allow_methods):
        assert not re.match(self.allow_methods_pattern, allow_methods)

    @pytest.mark.parametrize(
        "allow_headers",
        [
            "*",
            "**",
            "Bk-Token",
            "Bk-Token,Bk-User",
        ],
    )
    def test_allow_headers(self, allow_headers):
        assert re.match(self.allow_headers_pattern, allow_headers)

    @pytest.mark.parametrize(
        "allow_headers",
        [
            "",
            "Bk-Token, Bk-User",
            "Bk_Token",
        ],
    )
    def test_allow_headers__error(self, allow_headers):
        assert not re.match(self.allow_headers_pattern, allow_headers)

    @pytest.mark.parametrize(
        "expose_headers",
        [
            "",
            "*",
            "**",
            "Bk-Token",
            "Bk-Token,Bk-User",
        ],
    )
    def test_expose_headers(self, expose_headers):
        assert re.match(self.expose_headers_pattern, expose_headers)
