import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.validators import (
    MAX_LOOKUP_NAMES,
    validate_comma_separated_ints,
    validate_comma_separated_names,
)


def test_validate_comma_separated_names_normalizes_and_deduplicates():
    assert validate_comma_separated_names(
        " gateway-b,gateway-a,gateway-b ",
        max_count_error="最多 {max_count} 个",
    ) == ["gateway-b", "gateway-a"]


def test_validate_comma_separated_names_requires_values():
    with pytest.raises(ValidationError):
        validate_comma_separated_names(
            ", ,",
            required=True,
            required_error="不能为空",
            max_count_error="最多 {max_count} 个",
        )


def test_validate_comma_separated_names_rejects_over_limit():
    with pytest.raises(ValidationError) as exc_info:
        validate_comma_separated_names(
            ",".join(f"name-{i}" for i in range(MAX_LOOKUP_NAMES + 1)),
            max_count_error="最多 {max_count} 个",
        )

    assert str(exc_info.value.detail) == "[ErrorDetail(string='最多 50 个', code='invalid')]"


def test_validate_comma_separated_ints_parses_ids():
    assert validate_comma_separated_ints(
        " 1,2,2 ",
        invalid_error="invalid",
        max_count_error="最多 {max_count} 个",
    ) == [1, 2, 2]


def test_validate_comma_separated_ints_rejects_non_integer():
    with pytest.raises(ValidationError):
        validate_comma_separated_ints(
            "1,abc",
            invalid_error="invalid",
            max_count_error="最多 {max_count} 个",
        )
