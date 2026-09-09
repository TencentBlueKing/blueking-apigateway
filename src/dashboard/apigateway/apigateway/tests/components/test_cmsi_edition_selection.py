"""Notification transport depends on edition, not tenant mode."""

import importlib.util

import pytest

from apigateway.components import bkcmsi


@pytest.mark.parametrize("multi_tenant", [False, True])
@pytest.mark.parametrize("edition, expected", [("ee", "BKCMSIGateway"), ("te", "CMSIComponent")])
def test_notification_transport(settings, edition, multi_tenant, expected):
    settings.EDITION = edition
    settings.ENABLE_MULTI_TENANT_MODE = multi_tenant
    # Load a separate module so selection tests do not replace other tests' clients.
    spec = importlib.util.spec_from_file_location("apigateway.components._cmsi_selection", bkcmsi.__file__)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert type(module.cmsi_component).__name__ == expected


def test_gateway_im_returns_failure_without_aborting_other_channels():
    success, message = bkcmsi.BKCMSIGateway().send_im("default", {})
    assert success is False
    assert message
