import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.resource.legacy_serializers import (
    LegacyResourceHostSLZ,
    LegacyTransformHeadersSLZ,
    LegacyUpstreamsSLZ,
)


class TestLegacyResourceHostSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {"host": "http://demo.com"},
                {"host": "http://demo.com", "weight": 100},
                None,
            ),
            (
                {"host": "http://demo.com", "weight": 10},
                {"host": "http://demo.com", "weight": 10},
                None,
            ),
            (
                {},
                None,
                ValidationError,
            ),
            (
                {"host": "demo.com", "weight": 10},
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_error):
        slz = LegacyResourceHostSLZ(data=data)
        if not expected_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(expected_error):
            slz.is_valid(raise_exception=True)


class TestLegacyUpstreamsSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {},
                {},
                None,
            ),
            (
                {"hosts": [{"host": "http://demo.com"}], "loadbalance": "roundrobin"},
                {"hosts": [{"host": "http://demo.com"}], "loadbalance": "roundrobin"},
                None,
            ),
            (
                {"hosts": [{"host": "http://demo.com"}]},
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_error):
        slz = LegacyUpstreamsSLZ(data=data)
        if not expected_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(expected_error):
            slz.is_valid(raise_exception=True)


class TestLegacyTransformHeadersSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {},
                {},
                None,
            ),
            (
                {"set": {}, "delete": []},
                {"set": {}, "delete": []},
                None,
            ),
            (
                {"set": {"X-Token": "test"}, "delete": []},
                {"set": {"X-Token": "test"}, "delete": []},
                None,
            ),
            (
                {"set": {"X_Token": "test"}, "delete": ["X-Token"]},
                None,
                ValidationError,
            ),
            (
                {"set": {"": "test"}, "delete": []},
                None,
                ValidationError,
            ),
            (
                {"set": {"a" * 101: "test"}, "delete": []},
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_error):
        slz = LegacyTransformHeadersSLZ(data=data)
        if not expected_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(expected_error):
            slz.is_valid(raise_exception=True)
