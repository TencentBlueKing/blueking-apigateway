from types import SimpleNamespace

import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.tenant import get_request_tenant_id


def test_get_request_tenant_id_returns_none_in_single_tenant_mode(settings):
    settings.ENABLE_MULTI_TENANT_MODE = False

    assert get_request_tenant_id(SimpleNamespace()) is None


def test_get_request_tenant_id_returns_request_tenant_in_multi_tenant_mode(settings):
    settings.ENABLE_MULTI_TENANT_MODE = True

    assert get_request_tenant_id(SimpleNamespace(tenant_id="tenant-a")) == "tenant-a"


def test_get_request_tenant_id_rejects_missing_tenant_in_multi_tenant_mode(settings):
    settings.ENABLE_MULTI_TENANT_MODE = True

    with pytest.raises(ValidationError, match="tenant_id is required in multi-tenant mode"):
        get_request_tenant_id(SimpleNamespace(tenant_id=None))
