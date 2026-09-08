"""EE must start and expose its APIs without an ESB database or application."""

import pytest
from django.conf import settings
from django.urls import Resolver404, resolve


def test_ee_has_no_esb_database_or_app():
    assert "bkcore" not in settings.DATABASES
    assert not any(name.startswith("apigateway.apps.esb") for name in settings.INSTALLED_APPS)


@pytest.mark.parametrize(
    "path",
    [
        "/backend/api/v2/inner/esb/systems/",
        "/backend/esb/systems/",
        "/backend/docs/esb/boards/default/systems/",
    ],
)
def test_ee_does_not_register_esb_apis(path):
    with pytest.raises(Resolver404):
        resolve(path)
