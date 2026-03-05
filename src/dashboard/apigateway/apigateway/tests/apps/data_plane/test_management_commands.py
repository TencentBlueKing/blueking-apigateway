import json
from unittest.mock import patch

import pytest
from ddf import G
from django.core.management.base import CommandError

from apigateway.apps.data_plane.constants import DataPlaneStatusEnum
from apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane import Command as BindCommand
from apigateway.apps.data_plane.management.commands.create_data_plane import Command as CreateCommand
from apigateway.apps.data_plane.management.commands.unbind_gateways_from_data_plane import Command as UnbindCommand
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db

BK_KRILL_ENCRYPT_SECRET_KEY = "PIMCuSRiVqBg5eSzQqZZrOhGFSUtrlS-8_JlIpjHt0A="


@pytest.fixture(autouse=True)
def setup_crypto(settings):
    settings.BK_CRYPTO_TYPE = "CLASSIC"
    settings.ENCRYPT_CIPHER_TYPE = "FernetCipher"
    settings.BKKRILL_ENCRYPT_SECRET_KEY = BK_KRILL_ENCRYPT_SECRET_KEY


class TestCreateDataPlaneCommand:
    def test_create_success(self):
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
    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.trigger_gateway_publish")
    def test_bind_success(self, mock_trigger_gateway_publish, tmp_path):
        mock_trigger_gateway_publish.return_value = True
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

    @patch("apigateway.apps.data_plane.management.commands.bind_gateways_to_data_plane.trigger_gateway_publish")
    def test_bind_publish_failed_should_rollback_binding(self, mock_trigger_gateway_publish, tmp_path):
        mock_trigger_gateway_publish.return_value = False
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

        assert not GatewayDataPlaneBinding.objects.filter(gateway_id=gateway.id, data_plane_id=data_plane.id).exists()


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
