import pytest

from apigateway.apis.backend_config import restore_masked_header_values


def _config(secret: str) -> dict:
    return {"instances": [{"auth": {"header": {"Authorization": secret}}}]}


@pytest.mark.parametrize(
    ("incoming_secret", "expected_secret"),
    [
        ("Be****et", "Bearer secret"),
        ("ab****cd", "ab****cd"),
    ],
)
def test_restore_masked_header_values_only_restores_the_existing_display_mask(incoming_secret, expected_secret):
    config = _config(incoming_secret)

    restore_masked_header_values(config, _config("Bearer secret"))

    assert config["instances"][0]["auth"]["header"]["Authorization"] == expected_secret
