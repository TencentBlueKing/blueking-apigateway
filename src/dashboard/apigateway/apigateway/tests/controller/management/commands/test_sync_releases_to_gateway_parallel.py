from unittest import mock

import pytest
from ddf import G

from apigateway.controller.management.commands.sync_releases_to_gateway_parallel import sync_gateway
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestSyncGateway:
    @mock.patch("apigateway.controller.management.commands.sync_releases_to_gateway_parallel.logger")
    @mock.patch(
        "apigateway.controller.management.commands.sync_releases_to_gateway_parallel.publish.trigger_gateway_publish"
    )
    @mock.patch("django.db.connection.close")
    def test_returns_gateway_name_when_publish_raises(self, mock_close, mock_trigger_gateway_publish, mock_logger):
        gateway = G(Gateway, name="test-gateway")
        mock_trigger_gateway_publish.side_effect = RuntimeError("boom")

        result = sync_gateway(gateway)

        assert result == gateway.name
        mock_close.assert_called_once()
        mock_logger.exception.assert_called_once_with(
            "syncing release for gateway %s failed with exception", gateway.name
        )
