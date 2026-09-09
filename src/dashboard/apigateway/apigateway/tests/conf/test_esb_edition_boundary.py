"""Shared routing and configuration preserve only TE ESB integrations."""

import pytest
from django.conf import settings
from django.urls import Resolver404, resolve


def test_esb_database_and_application_boundary():
    enabled = settings.EDITION == "te"
    assert ("bkcore" in settings.DATABASES) is enabled
    assert ("apigateway.apps.esb.bkcore" in settings.INSTALLED_APPS) is enabled


@pytest.mark.parametrize(
    "path",
    [
        "/backend/api/v2/inner/esb/systems/",
        "/backend/api/v1/esb/systems/",
        "/backend/docs/esb/boards/ieod/systems/",
    ],
)
def test_esb_permission_and_document_routes(path):
    if settings.EDITION == "te":
        assert resolve(path).func is not None
    else:
        with pytest.raises(Resolver404):
            resolve(path)


def test_removed_component_management_route():
    with pytest.raises(Resolver404):
        resolve("/backend/esb/systems/")
