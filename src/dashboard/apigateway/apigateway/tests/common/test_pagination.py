import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apigateway.common.pagination import BoundedLimitOffsetPagination


class _ExamplePagination(BoundedLimitOffsetPagination):
    default_limit = 10
    max_limit = 20


@pytest.mark.parametrize(
    ("query", "method_name"),
    [
        ({"limit": "invalid"}, "get_limit"),
        ({"limit": 0}, "get_limit"),
        ({"limit": 21}, "get_limit"),
        ({"offset": "invalid"}, "get_offset"),
        ({"offset": -1}, "get_offset"),
    ],
)
def test_bounded_limit_offset_pagination_rejects_invalid_params(query, method_name):
    request = Request(APIRequestFactory().get("/", query))
    pagination = _ExamplePagination()

    with pytest.raises(ValidationError):
        getattr(pagination, method_name)(request)


def test_bounded_limit_offset_pagination_accepts_valid_params():
    request = Request(APIRequestFactory().get("/", {"limit": 20, "offset": 5}))
    pagination = _ExamplePagination()

    assert pagination.get_limit(request) == 20
    assert pagination.get_offset(request) == 5
