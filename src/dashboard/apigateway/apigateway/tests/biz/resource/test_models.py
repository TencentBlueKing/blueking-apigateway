import pytest

from apigateway.biz.resource.models import ResourceBackendConfig


class TestResourceBackendConfig:
    @pytest.mark.parametrize(
        "data, expected, expected_legacy_upstreams, expected_legacy_transform_headers",
        [
            (
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                },
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                },
                None,
                None,
            ),
            (
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                    "legacy_upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [{"host": "http://foo.com", "weight": 10}],
                    },
                    "legacy_transform_headers": {
                        "set": {"x-token": "test"},
                        "delete": ["x-token"],
                    },
                },
                {
                    "method": "GET",
                    "path": "/user",
                    "match_subpath": True,
                    "timeout": 10,
                },
                {
                    "loadbalance": "roundrobin",
                    "hosts": [{"host": "http://foo.com", "weight": 10}],
                },
                {
                    "set": {"x-token": "test"},
                    "delete": ["x-token"],
                },
            ),
        ],
    )
    def test_dict(self, data, expected, expected_legacy_upstreams, expected_legacy_transform_headers):
        config = ResourceBackendConfig.parse_obj(data)
        assert config.legacy_upstreams == expected_legacy_upstreams
        assert config.legacy_transform_headers == expected_legacy_transform_headers
        assert config.dict() == expected
