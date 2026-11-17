import datetime
from io import StringIO
from unittest import mock

import pytest
from ddf import G
from django.core.management import CommandError, call_command

from apigateway.controller.management.commands.sync_releases_to_gateway_parallel import sync_gateway
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, ReleaseHistory

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


class TestCommand:
    @pytest.fixture
    def released_gateways(self):
        def _gateway_with_history(name, created_time, status=GatewayStatusEnum.ACTIVE.value):
            gateway = G(Gateway, name=name, status=status)
            history = G(ReleaseHistory, gateway=gateway)
            ReleaseHistory.objects.filter(id=history.id).update(created_time=created_time)
            return gateway

        since = datetime.datetime(2026, 11, 17, 10, 0, tzinfo=datetime.timezone.utc)
        return {
            "since": since,
            "before": _gateway_with_history("released-before", since - datetime.timedelta(seconds=1)),
            "at": _gateway_with_history("released-at", since),
            "after": _gateway_with_history("released-after", since + datetime.timedelta(hours=1)),
            "inactive": _gateway_with_history(
                "released-inactive", since + datetime.timedelta(hours=1), status=GatewayStatusEnum.INACTIVE.value
            ),
        }

    def test_dry_run_lists_active_gateways_released_since(self, released_gateways):
        stdout = StringIO()

        with mock.patch(
            "apigateway.controller.management.commands.sync_releases_to_gateway_parallel.Pool"
        ) as mock_pool:
            call_command(
                "sync_releases_to_gateway_parallel",
                "--released-since",
                released_gateways["since"].isoformat(),
                "--dry-run",
                stdout=stdout,
                stderr=StringIO(),
            )

        assert stdout.getvalue().strip() == "released-after released-at"
        mock_pool.assert_not_called()

    def test_dry_run_combines_released_since_with_gateway_names(self, released_gateways):
        stdout = StringIO()

        call_command(
            "sync_releases_to_gateway_parallel",
            "--gateway-names",
            "released-at",
            "released-before",
            "--released-since",
            released_gateways["since"].isoformat(),
            "--dry-run",
            stdout=stdout,
            stderr=StringIO(),
        )

        assert stdout.getvalue().strip() == "released-at"

    def test_naive_released_since_uses_current_timezone(self, settings, released_gateways):
        settings.TIME_ZONE = "Asia/Shanghai"
        stdout = StringIO()

        # 2026-11-17 18:00 Asia/Shanghai == 2026-11-17 10:00 UTC
        call_command(
            "sync_releases_to_gateway_parallel",
            "--released-since",
            "2026-11-17 18:00:00",
            "--dry-run",
            stdout=stdout,
            stderr=StringIO(),
        )

        assert stdout.getvalue().strip() == "released-after released-at"

    def test_invalid_released_since(self):
        with pytest.raises(CommandError, match="invalid --released-since"):
            call_command("sync_releases_to_gateway_parallel", "--released-since", "yesterday", "--dry-run")

    def test_publishes_matched_gateways(self, released_gateways):
        with mock.patch(
            "apigateway.controller.management.commands.sync_releases_to_gateway_parallel.Pool"
        ) as mock_pool:
            pool = mock_pool.return_value.__enter__.return_value
            pool.map.return_value = [None, None]

            call_command(
                "sync_releases_to_gateway_parallel",
                "--released-since",
                released_gateways["since"].isoformat(),
            )

        _, gateways = pool.map.call_args.args
        assert sorted(gateway.name for gateway in gateways) == ["released-after", "released-at"]
