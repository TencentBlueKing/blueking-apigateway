import datetime
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from ddf import G
from django.core.management import CommandError, call_command

from apigateway.controller.management.commands.sync_releases_to_gateway_parallel import sync_gateway
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, Release, ReleaseHistory

pytestmark = pytest.mark.django_db

# 与设计文档 7.4 回滚第 5 步的脚本保持逐字一致
RESTORE_RUNBOOK_SNIPPET = """read -r -d '' -a gateway_names < gateways.txt || true
if [ "${#gateway_names[@]}" -gt 0 ]; then
  GATEWAY_NAMES="${gateway_names[*]}" python manage.py shell -c '
import multiprocessing, os
multiprocessing.set_start_method("fork", force=True)
from django.core.management import call_command
call_command("sync_releases_to_gateway_parallel", gateway_names=os.environ["GATEWAY_NAMES"].split())
'
else
  echo "no gateway to restore"
fi
"""
DESIGN_DOC = Path(__file__).resolve().parents[8] / "docs" / "design" / "resource-oauth2-app-access-design.md"


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

    def test_dry_run_includes_gateways_distributed_without_release_history(self, released_gateways):
        since = released_gateways["since"]

        def _gateway_with_release(name, updated_time):
            gateway = G(Gateway, name=name, status=GatewayStatusEnum.ACTIVE.value)
            release = G(Release, gateway=gateway)
            Release.objects.filter(id=release.id).update(updated_time=updated_time)
            return gateway

        # CLI_SYNC 只更新 Release.updated_time，不写 ReleaseHistory
        _gateway_with_release("cli-synced-after", since + datetime.timedelta(minutes=5))
        _gateway_with_release("cli-synced-before", since - datetime.timedelta(minutes=5))
        # 两个条件同时命中只出现一次
        Release.objects.filter(
            id=G(Release, gateway=released_gateways["after"]).id,
        ).update(updated_time=since + datetime.timedelta(minutes=5))
        stdout = StringIO()

        call_command(
            "sync_releases_to_gateway_parallel",
            "--released-since",
            since.isoformat(),
            "--dry-run",
            stdout=stdout,
            stderr=StringIO(),
        )

        assert stdout.getvalue().strip() == "cli-synced-after released-after released-at"

    def test_dry_run_prints_empty_output_when_nothing_matches(self, released_gateways):
        stdout = StringIO()
        stderr = StringIO()

        call_command(
            "sync_releases_to_gateway_parallel",
            "--released-since",
            (released_gateways["since"] + datetime.timedelta(days=1)).isoformat(),
            "--dry-run",
            stdout=stdout,
            stderr=stderr,
        )

        assert stdout.getvalue() == ""
        assert "0 gateways matched" in stderr.getvalue()

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


class TestRestoreRunbook:
    def test_restore_runbook_snippet_matches_design_doc(self):
        if not DESIGN_DOC.exists():
            pytest.skip("design doc is not available outside the repository checkout")

        assert RESTORE_RUNBOOK_SNIPPET in DESIGN_DOC.read_text(encoding="utf-8")

    @pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required")
    @pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="fork is required")
    @pytest.mark.parametrize(
        "content, expected_gateways",
        [
            ("", None),
            (" \n\t\n", None),
            ("gw-a gw-b\n", ["gw-a", "gw-b"]),
        ],
    )
    def test_restore_runbook_invokes_command_only_for_selected_gateways(self, tmp_path, content, expected_gateways):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        fake_python = bin_dir / "python"
        fake_python.write_text('#!/bin/sh\nexec "$RUNBOOK_TEST_PYTHON" "$@"\n')
        fake_python.chmod(0o755)
        (tmp_path / "manage.py").write_text(
            """import json
import multiprocessing
import sys
from pathlib import Path
from unittest.mock import patch

assert sys.argv[1:3] == ["shell", "-c"]
with patch("django.core.management.call_command") as call_command:
    exec(sys.argv[3])
    args, kwargs = call_command.call_args
    Path("called.json").write_text(json.dumps([multiprocessing.get_start_method(), args, kwargs]))
"""
        )
        (tmp_path / "gateways.txt").write_text(content)

        result = subprocess.run(
            ["bash", "-c", RESTORE_RUNBOOK_SNIPPET],
            cwd=tmp_path,
            env={
                **os.environ,
                "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                "RUNBOOK_TEST_PYTHON": sys.executable,
            },
            capture_output=True,
            text=True,
            check=True,
        )

        called = tmp_path / "called.json"
        if expected_gateways is None:
            assert not called.exists()
            assert result.stdout == "no gateway to restore\n"
        else:
            assert json.loads(called.read_text()) == [
                "fork",
                ["sync_releases_to_gateway_parallel"],
                {"gateway_names": expected_gateways},
            ]
