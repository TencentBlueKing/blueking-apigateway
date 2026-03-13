import json
from unittest.mock import patch

import pytest
from ddf import G
from django.core.management.base import CommandError

from apigateway.apps.data_plane.constants import DataPlaneStatusEnum
from apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane import Command as BindCommand
from apigateway.apps.data_plane.management.commands.create_data_plane import Command as CreateCommand
from apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways import Command as DeployCommand
from apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane import Command as UnbindCommand
from apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways import Command as UndeployCommand
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.controller.constants import DELETE_PUBLISH_ID, NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Stage

pytestmark = pytest.mark.django_db

BK_KRILL_ENCRYPT_SECRET_KEY = "PIMCuSRiVqBg5eSzQqZZrOhGFSUtrlS-8_JlIpjHt0A="


@pytest.fixture(autouse=True)
def setup_crypto(settings):
    settings.BK_CRYPTO_TYPE = "CLASSIC"
    settings.ENCRYPT_CIPHER_TYPE = "FernetCipher"
    settings.BKKRILL_ENCRYPT_SECRET_KEY = BK_KRILL_ENCRYPT_SECRET_KEY


class TestCreateDataPlaneCommand:
    @patch("apigateway.apps.data_plane.management.commands.create_data_plane.GlobalResourceDistributor")
    def test_create_success_triggers_global_sync(self, mock_distributor_cls):
        mock_distributor_cls.return_value.distribute.return_value = (True, "")
        cmd = CreateCommand()
        etcd_config = {
            "host": "127.0.0.1",
            "port": 2379,
            "user": "root",
            "password": "secret",
            "ca_cert": "/tmp/ca",
            "cert_cert": "/tmp/cert",
            "cert_key": "/tmp/key",
        }

        cmd.handle(
            name="plane-a",
            description="desc",
            bk_api_url_tmpl="https://{api_name}.example.com",
            status=DataPlaneStatusEnum.ACTIVE.value,
            etcd_config=json.dumps(etcd_config),
            etcd_namespace_prefix="foo/bar",
            created_by="tester",
        )

        data_plane = DataPlane.objects.get(name="plane-a")
        assert data_plane.etcd_namespace_prefix == "/foo/bar"
        assert data_plane.etcd_configs == etcd_config
        mock_distributor_cls.assert_called_once_with(data_plane=data_plane)
        mock_distributor_cls.return_value.distribute.assert_called_once()

    @patch("apigateway.apps.data_plane.management.commands.create_data_plane.GlobalResourceDistributor")
    @patch("apigateway.apps.data_plane.management.commands.create_data_plane.logger")
    def test_create_success(self, mock_logger, mock_distributor_cls):
        mock_distributor_cls.return_value.distribute.return_value = (False, "sync failed")
        cmd = CreateCommand()
        etcd_config = {
            "host": "127.0.0.1",
            "port": 2379,
            "user": "root",
            "password": "secret",
            "ca_cert": "/tmp/ca",
            "cert_cert": "/tmp/cert",
            "cert_key": "/tmp/key",
        }

        cmd.handle(
            name="plane-a",
            description="desc",
            bk_api_url_tmpl="https://{api_name}.example.com",
            status=DataPlaneStatusEnum.ACTIVE.value,
            etcd_config=json.dumps(etcd_config),
            etcd_namespace_prefix="foo/bar",
            created_by="tester",
        )

        data_plane = DataPlane.objects.get(name="plane-a")
        assert data_plane.etcd_namespace_prefix == "/foo/bar"
        assert data_plane.etcd_configs == etcd_config
        mock_logger.error.assert_called_once()

    def test_create_with_invalid_etcd_config_keys_raises(self):
        cmd = CreateCommand()
        etcd_config = {"host": "127.0.0.1", "port": 2379}

        with pytest.raises(CommandError, match="etcd_config missing required keys"):
            cmd.handle(
                name="plane-a",
                description="desc",
                bk_api_url_tmpl="https://{api_name}.example.com",
                status=DataPlaneStatusEnum.ACTIVE.value,
                etcd_config=json.dumps(etcd_config),
                etcd_namespace_prefix="/foo/bar",
                created_by="tester",
            )


class TestBindGatewaysToDataPlaneCommand:
    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_success(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_publish_failed_should_rollback_binding(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = False
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_already_bound_skipped(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        mock_rolling_update_release.assert_not_called()
        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).count() == 1

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_dry_run_no_binding_created(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=True,
        )

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()
        mock_rolling_update_release.assert_not_called()

    def test_bind_data_plane_not_found_raises(self, tmp_path):
        gateway = G(Gateway, name="gw-a")

        cmd = BindCommand()
        with pytest.raises(CommandError, match="data plane not found"):
            cmd.handle(
                gateway_names=gateway.name,
                gateway_names_file="",
                data_plane_name="nonexistent-plane",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "bind.log"),
                operator="tester",
                dry_run=False,
            )

    def test_bind_gateway_not_found_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")

        cmd = BindCommand()
        with pytest.raises(CommandError, match="some gateway names not found in the database"):
            cmd.handle(
                gateway_names="nonexistent-gw",
                gateway_names_file="",
                data_plane_name=data_plane.name,
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "bind.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_skip_gateway_names(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names=gateway.name,
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()
        mock_rolling_update_release.assert_not_called()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_inactive_gateway_no_publish(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.INACTIVE.value)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()
        mock_rolling_update_release.assert_not_called()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_active_gateway_no_active_stages_no_publish(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.INACTIVE.value)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()
        mock_rolling_update_release.assert_not_called()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_multiple_gateways_mixed_results(self, mock_rolling_update_release, tmp_path):
        """One gateway succeeds, another is skipped (already bound)."""
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gw_a = G(Gateway, name="gw-a")
        gw_b = G(Gateway, name="gw-b")
        G(GatewayDataPlaneBinding, gateway=gw_b, data_plane=data_plane)

        cmd = BindCommand()
        cmd.handle(
            gateway_names="gw-a,gw-b",
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gw_a.id, data_plane_id=data_plane.id).exists()
        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gw_b.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_exception_during_bind_counted_as_failed(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.side_effect = Exception("unexpected error")
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        log_content = (tmp_path / "bind.log").read_text()
        assert '"result": "failed"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_with_gateway_names_file(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")

        names_file = tmp_path / "gateways.txt"
        names_file.write_text("gw-a\n")

        cmd = BindCommand()
        cmd.handle(
            gateway_names="",
            gateway_names_file=str(names_file),
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    def test_bind_empty_data_plane_name_raises(self, tmp_path):
        gateway = G(Gateway, name="gw-a")

        cmd = BindCommand()
        with pytest.raises(CommandError, match="data_plane_name should not be empty"):
            cmd.handle(
                gateway_names=gateway.name,
                gateway_names_file="",
                data_plane_name="  ",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "bind.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_active_gateway_multiple_stages_publish_all(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage1 = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        stage2 = G(Stage, gateway=gateway, name="stag", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage1)
        G(Release, gateway=gateway, stage=stage2)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert mock_rolling_update_release.call_count == 2
        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_second_stage_publish_fails_rollback(self, mock_rolling_update_release, tmp_path):
        """First stage publishes ok, second fails -> binding should be rolled back."""
        mock_rolling_update_release.side_effect = [True, False]
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage1 = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        stage2 = G(Stage, gateway=gateway, name="stag", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage1)
        G(Release, gateway=gateway, stage=stage2)

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.rolling_update_release")
    def test_bind_skip_gateway_names_file(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")

        skip_file = tmp_path / "skip.txt"
        skip_file.write_text("gw-a\n")

        cmd = BindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file=str(skip_file),
            log_file=str(tmp_path / "bind.log"),
            operator="tester",
            dry_run=False,
        )

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()
        mock_rolling_update_release.assert_not_called()


class TestUnbindGatewaysFromDataPlaneCommand:
    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_last_binding_blocked_without_force(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_last_binding_allowed_with_force(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=True,
        )

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_not_last_binding_allowed_without_force(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = True
        data_plane_a = G(DataPlane, name="plane-a")
        data_plane_b = G(DataPlane, name="plane-b")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_a)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_b)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane_a.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        assert not GatewayDataPlaneBinding.objects.filter(
            gateway_id=gateway.id, data_plane_id=data_plane_a.id
        ).exists()
        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane_b.id).exists()

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_binding_not_found_skipped(self, mock_revoke_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        mock_revoke_release.assert_not_called()
        log_content = (tmp_path / "unbind.log").read_text()
        assert '"result": "skipped"' in log_content
        assert '"reason": "binding_not_found"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_dry_run_no_changes(self, mock_revoke_release, tmp_path):
        data_plane_a = G(DataPlane, name="plane-a")
        data_plane_b = G(DataPlane, name="plane-b")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_a)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_b)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane_a.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=True,
            force_unbind_last=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane_a.id).exists()
        mock_revoke_release.assert_not_called()

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_revoke_failed_keeps_binding(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = False
        data_plane_a = G(DataPlane, name="plane-a")
        data_plane_b = G(DataPlane, name="plane-b")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_a)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_b)
        G(Release, gateway=gateway)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane_a.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane_a.id).exists()
        log_content = (tmp_path / "unbind.log").read_text()
        assert '"result": "failed"' in log_content
        assert '"reason": "revoke_failed"' in log_content

    def test_unbind_data_plane_not_found_raises(self, tmp_path):
        gateway = G(Gateway, name="gw-a")

        cmd = UnbindCommand()
        with pytest.raises(CommandError, match="data plane not found"):
            cmd.handle(
                gateway_names=gateway.name,
                gateway_names_file="",
                data_plane_name="nonexistent-plane",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "unbind.log"),
                operator="tester",
                dry_run=False,
                force_unbind_last=False,
            )

    def test_unbind_gateway_not_found_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")

        cmd = UnbindCommand()
        with pytest.raises(CommandError, match="some gateway names not found in the database"):
            cmd.handle(
                gateway_names="nonexistent-gw",
                gateway_names_file="",
                data_plane_name=data_plane.name,
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "unbind.log"),
                operator="tester",
                dry_run=False,
                force_unbind_last=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_skip_gateway_names(self, mock_revoke_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane.name,
            skip_gateway_names=gateway.name,
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        assert GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()
        mock_revoke_release.assert_not_called()
        log_content = (tmp_path / "unbind.log").read_text()
        assert '"reason": "skipped_by_argument"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_exception_counted_as_failed(self, mock_revoke_release, tmp_path):
        mock_revoke_release.side_effect = Exception("unexpected error")
        data_plane_a = G(DataPlane, name="plane-a")
        data_plane_b = G(DataPlane, name="plane-b")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_a)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_b)
        G(Release, gateway=gateway)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane_a.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        log_content = (tmp_path / "unbind.log").read_text()
        assert '"result": "failed"' in log_content

    def test_unbind_empty_data_plane_name_raises(self, tmp_path):
        gateway = G(Gateway, name="gw-a")

        cmd = UnbindCommand()
        with pytest.raises(CommandError, match="data_plane_name should not be empty"):
            cmd.handle(
                gateway_names=gateway.name,
                gateway_names_file="",
                data_plane_name="  ",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "unbind.log"),
                operator="tester",
                dry_run=False,
                force_unbind_last=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane.revoke_release")
    def test_unbind_no_releases_still_unbinds(self, mock_revoke_release, tmp_path):
        """Gateway has no releases, revoke loop is skipped, binding is removed."""
        data_plane_a = G(DataPlane, name="plane-a")
        data_plane_b = G(DataPlane, name="plane-b")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_a)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane_b)

        cmd = UnbindCommand()
        cmd.handle(
            gateway_names=gateway.name,
            gateway_names_file="",
            data_plane_name=data_plane_a.name,
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "unbind.log"),
            operator="tester",
            dry_run=False,
            force_unbind_last=False,
        )

        assert not GatewayDataPlaneBinding.objects.filter(
            gateway_id=gateway.id, data_plane_id=data_plane_a.id
        ).exists()
        mock_revoke_release.assert_not_called()


class TestDeployDataPlaneGatewaysCommand:
    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_all_success(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        release = G(Release, gateway=gateway, stage=stage)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_rolling_update_release.assert_called_once_with(
            gateway_id=gateway.id,
            publish_id=NO_NEED_REPORT_EVENT_PUBLISH_ID,
            release_id=release.id,
            data_plane_id=data_plane.id,
        )

    def test_deploy_with_unbound_gateway_name_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=Gateway.objects.get(name="gw-a"), data_plane=data_plane)

        cmd = DeployCommand()
        with pytest.raises(CommandError, match="not bound to the data_plane"):
            cmd.handle(
                data_plane_name=data_plane.name,
                deploy_all=False,
                gateway_names="gw-not-bound",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "deploy.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_dry_run_no_publish(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=True,
        )

        mock_rolling_update_release.assert_not_called()

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_inactive_gateway_skipped(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.INACTIVE.value)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_rolling_update_release.assert_not_called()
        log_content = (tmp_path / "deploy.log").read_text()
        assert '"result": "skipped"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_no_active_stages_skipped(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.INACTIVE.value)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_rolling_update_release.assert_not_called()
        log_content = (tmp_path / "deploy.log").read_text()
        assert '"result": "skipped"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_publish_fails(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = False
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        log_content = (tmp_path / "deploy.log").read_text()
        assert '"result": "failed"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_specific_gateways_success(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gw_a = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        gw_b = G(Gateway, name="gw-b", status=GatewayStatusEnum.ACTIVE.value)
        stage_a = G(Stage, gateway=gw_a, name="prod", status=StageStatusEnum.ACTIVE.value)
        stage_b = G(Stage, gateway=gw_b, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gw_a, stage=stage_a)
        G(Release, gateway=gw_b, stage=stage_b)
        G(GatewayDataPlaneBinding, gateway=gw_a, data_plane=data_plane)
        G(GatewayDataPlaneBinding, gateway=gw_b, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=False,
            gateway_names="gw-a",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        assert mock_rolling_update_release.call_count == 1
        call_kwargs = mock_rolling_update_release.call_args
        assert call_kwargs[1]["gateway_id"] == gw_a.id

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_skip_gateway_names(self, mock_rolling_update_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names=gateway.name,
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_rolling_update_release.assert_not_called()
        log_content = (tmp_path / "deploy.log").read_text()
        assert '"reason": "skipped_by_argument"' in log_content

    def test_deploy_data_plane_not_found_raises(self, tmp_path):
        cmd = DeployCommand()
        with pytest.raises(CommandError, match="data plane not found"):
            cmd.handle(
                data_plane_name="nonexistent-plane",
                deploy_all=True,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "deploy.log"),
                operator="tester",
                dry_run=False,
            )

    def test_deploy_no_gateways_bound_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")

        cmd = DeployCommand()
        with pytest.raises(CommandError, match="no gateways bound to data plane"):
            cmd.handle(
                data_plane_name=data_plane.name,
                deploy_all=True,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "deploy.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_exception_counted_as_failed(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.side_effect = Exception("unexpected error")
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        log_content = (tmp_path / "deploy.log").read_text()
        assert '"result": "failed"' in log_content

    def test_deploy_empty_data_plane_name_raises(self, tmp_path):
        cmd = DeployCommand()
        with pytest.raises(CommandError, match="data_plane_name should not be empty"):
            cmd.handle(
                data_plane_name="  ",
                deploy_all=True,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "deploy.log"),
                operator="tester",
                dry_run=False,
            )

    def test_deploy_empty_gateway_names_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        with pytest.raises(CommandError, match="no valid gateway names provided"):
            cmd.handle(
                data_plane_name=data_plane.name,
                deploy_all=False,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "deploy.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_multiple_stages_all_published(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage1 = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        stage2 = G(Stage, gateway=gateway, name="stag", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage1)
        G(Release, gateway=gateway, stage=stage2)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        assert mock_rolling_update_release.call_count == 2

    @patch("apigateway.apps.data_plane.management.commands.deploy_data_plane_gateways.rolling_update_release")
    def test_deploy_second_stage_fails_marks_failed(self, mock_rolling_update_release, tmp_path):
        mock_rolling_update_release.side_effect = [True, False]
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a", status=GatewayStatusEnum.ACTIVE.value)
        stage1 = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        stage2 = G(Stage, gateway=gateway, name="stag", status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=gateway, stage=stage1)
        G(Release, gateway=gateway, stage=stage2)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = DeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            deploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "deploy.log"),
            operator="tester",
            dry_run=False,
        )

        log_content = (tmp_path / "deploy.log").read_text()
        assert '"result": "failed"' in log_content


class TestUndeployDataPlaneGatewaysCommand:
    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_all_success(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        release = G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_revoke_release.assert_called_once_with(
            release_id=release.id,
            publish_id=DELETE_PUBLISH_ID,
            data_plane_id=data_plane.id,
        )

    def test_undeploy_with_unbound_gateway_name_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        with pytest.raises(CommandError, match="not bound to the data_plane"):
            cmd.handle(
                data_plane_name=data_plane.name,
                undeploy_all=False,
                gateway_names="gw-not-bound",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "undeploy.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_dry_run_no_revoke(self, mock_revoke_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=True,
        )

        mock_revoke_release.assert_not_called()

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_no_releases_success(self, mock_revoke_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_revoke_release.assert_not_called()
        log_content = (tmp_path / "undeploy.log").read_text()
        assert '"result": "success"' in log_content
        assert '"reason": "no_releases"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_revoke_fails(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = False
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        log_content = (tmp_path / "undeploy.log").read_text()
        assert '"result": "failed"' in log_content
        assert '"reason": "revoke_failed"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_specific_gateways(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gw_a = G(Gateway, name="gw-a")
        gw_b = G(Gateway, name="gw-b")
        G(Release, gateway=gw_a)
        G(GatewayDataPlaneBinding, gateway=gw_a, data_plane=data_plane)
        G(GatewayDataPlaneBinding, gateway=gw_b, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=False,
            gateway_names="gw-a",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_revoke_release.assert_called_once()

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_skip_gateway_names(self, mock_revoke_release, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names=gateway.name,
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        mock_revoke_release.assert_not_called()
        log_content = (tmp_path / "undeploy.log").read_text()
        assert '"reason": "skipped_by_argument"' in log_content

    def test_undeploy_data_plane_not_found_raises(self, tmp_path):
        cmd = UndeployCommand()
        with pytest.raises(CommandError, match="data plane not found"):
            cmd.handle(
                data_plane_name="nonexistent-plane",
                undeploy_all=True,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "undeploy.log"),
                operator="tester",
                dry_run=False,
            )

    def test_undeploy_no_gateways_bound_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")

        cmd = UndeployCommand()
        with pytest.raises(CommandError, match="no gateways bound to data plane"):
            cmd.handle(
                data_plane_name=data_plane.name,
                undeploy_all=True,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "undeploy.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_exception_counted_as_failed(self, mock_revoke_release, tmp_path):
        mock_revoke_release.side_effect = Exception("unexpected error")
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        log_content = (tmp_path / "undeploy.log").read_text()
        assert '"result": "failed"' in log_content

    def test_undeploy_empty_data_plane_name_raises(self, tmp_path):
        cmd = UndeployCommand()
        with pytest.raises(CommandError, match="data_plane_name should not be empty"):
            cmd.handle(
                data_plane_name="  ",
                undeploy_all=True,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "undeploy.log"),
                operator="tester",
                dry_run=False,
            )

    def test_undeploy_empty_gateway_names_raises(self, tmp_path):
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        with pytest.raises(CommandError, match="no valid gateway names provided"):
            cmd.handle(
                data_plane_name=data_plane.name,
                undeploy_all=False,
                gateway_names="",
                skip_gateway_names="",
                skip_gateway_names_file="",
                log_file=str(tmp_path / "undeploy.log"),
                operator="tester",
                dry_run=False,
            )

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_multiple_releases_all_revoked(self, mock_revoke_release, tmp_path):
        mock_revoke_release.return_value = True
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(Release, gateway=gateway)
        G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        assert mock_revoke_release.call_count == 2
        log_content = (tmp_path / "undeploy.log").read_text()
        assert '"result": "success"' in log_content

    @patch("apigateway.apps.data_plane.management.commands.undeploy_data_plane_gateways.revoke_release")
    def test_undeploy_second_release_fails_stops(self, mock_revoke_release, tmp_path):
        mock_revoke_release.side_effect = [True, False]
        data_plane = G(DataPlane, name="plane-a")
        gateway = G(Gateway, name="gw-a")
        G(Release, gateway=gateway)
        G(Release, gateway=gateway)
        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        cmd = UndeployCommand()
        cmd.handle(
            data_plane_name=data_plane.name,
            undeploy_all=True,
            gateway_names="",
            skip_gateway_names="",
            skip_gateway_names_file="",
            log_file=str(tmp_path / "undeploy.log"),
            operator="tester",
            dry_run=False,
        )

        assert mock_revoke_release.call_count == 2
        log_content = (tmp_path / "undeploy.log").read_text()
        assert '"result": "failed"' in log_content
