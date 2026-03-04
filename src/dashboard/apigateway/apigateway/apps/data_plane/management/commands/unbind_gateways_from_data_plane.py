import logging
from importlib import import_module
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.data_plane.management.commands.gateway_data_plane_command_utils import (
    AuditWriter,
    parse_comma_separated_names,
    parse_gateway_names,
    parse_names_from_file,
)
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Unbind gateways from one data plane after synchronous revoke"

    def add_arguments(self, parser):
        parser.add_argument("--gateway-names", type=str, default="", help="Gateway names, comma separated")
        parser.add_argument(
            "--gateway-names-file",
            type=str,
            default="",
            help="Gateway names file, one gateway name per line",
        )
        parser.add_argument("--data-plane-name", type=str, required=True, help="Target data plane name")
        parser.add_argument(
            "--skip-gateway-names",
            type=str,
            default="",
            help="Gateway names to skip temporarily, comma separated",
        )
        parser.add_argument(
            "--skip-gateway-names-file",
            type=str,
            default="",
            help="Gateway names file to skip temporarily, one gateway name per line",
        )
        parser.add_argument("--log-file", type=str, required=True, help="Audit log file path")
        parser.add_argument("--operator", type=str, default="system", help="Operator username")

    def _revoke_gateway_releases(
        self, gateway: Any, data_plane_id: int, release_model: Any, revoke_release: Any, delete_publish_id: int
    ) -> bool:
        releases = release_model.objects.filter(gateway_id=gateway.id).all()
        for release in releases:
            ok = revoke_release(release_id=release.id, publish_id=delete_publish_id, data_plane_id=data_plane_id)
            if not ok:
                return False
        return True

    def handle(self, *args, **options):
        gateway_names = parse_gateway_names(options["gateway_names"], options["gateway_names_file"])
        skip_gateway_names = set(parse_comma_separated_names(options["skip_gateway_names"]))
        skip_gateway_names.update(parse_names_from_file(options["skip_gateway_names_file"], "skip gateway names file"))
        data_plane_name = options["data_plane_name"].strip()
        operator = options["operator"]
        audit_writer = AuditWriter(self.stdout, options["log_file"])
        gateway_model = apps.get_model("core", "Gateway")
        release_model = apps.get_model("core", "Release")
        controller_constants = import_module("apigateway.controller.constants")
        syncing_module = import_module("apigateway.controller.tasks.syncing")
        delete_publish_id = controller_constants.DELETE_PUBLISH_ID
        revoke_release = syncing_module.revoke_release

        if not data_plane_name:
            raise CommandError("data_plane_name should not be empty")

        data_plane = DataPlane.objects.filter(name=data_plane_name).first()
        if not data_plane:
            raise CommandError(f"data plane not found: {data_plane_name}")

        gateways = gateway_model.objects.filter(name__in=gateway_names)
        gateway_by_name = {gateway.name: gateway for gateway in gateways}

        success_count = 0
        skipped_count = 0
        failed_count = 0

        for gateway_name in gateway_names:
            if gateway_name in skip_gateway_names:
                skipped_count += 1
                audit_writer.write(
                    action="unbind_gateway_from_data_plane",
                    result="skipped",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="skipped_by_argument",
                    operator=operator,
                )
                continue

            gateway = gateway_by_name.get(gateway_name)
            if not gateway:
                failed_count += 1
                audit_writer.write(
                    action="unbind_gateway_from_data_plane",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="gateway_not_found",
                    operator=operator,
                )
                continue

            try:
                binding = GatewayDataPlaneBinding.objects.filter(
                    gateway_id=gateway.id,
                    data_plane_id=data_plane.id,
                ).first()
                if not binding:
                    skipped_count += 1
                    audit_writer.write(
                        action="unbind_gateway_from_data_plane",
                        result="skipped",
                        gateway_name=gateway.name,
                        gateway_id=gateway.id,
                        data_plane_name=data_plane.name,
                        data_plane_id=data_plane.id,
                        reason="binding_not_found",
                        operator=operator,
                    )
                    continue

                revoked = self._revoke_gateway_releases(
                    gateway,
                    data_plane.id,
                    release_model=release_model,
                    revoke_release=revoke_release,
                    delete_publish_id=delete_publish_id,
                )
                if not revoked:
                    failed_count += 1
                    audit_writer.write(
                        action="unbind_gateway_from_data_plane",
                        result="failed",
                        gateway_name=gateway.name,
                        gateway_id=gateway.id,
                        data_plane_name=data_plane.name,
                        data_plane_id=data_plane.id,
                        reason="revoke_failed",
                        operator=operator,
                    )
                    continue

                GatewayDataPlaneBinding.objects.unbind_gateway_from_data_plane(
                    gateway_id=gateway.id,
                    data_plane_id=data_plane.id,
                )

                success_count += 1
                audit_writer.write(
                    action="unbind_gateway_from_data_plane",
                    result="success",
                    gateway_name=gateway.name,
                    gateway_id=gateway.id,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                    operator=operator,
                )
            except Exception as err:  # pylint: disable=broad-except
                failed_count += 1
                logger.exception(
                    "failed to unbind gateway from data plane: gateway=%s, data_plane=%s",
                    gateway_name,
                    data_plane_name,
                )
                audit_writer.write(
                    action="unbind_gateway_from_data_plane",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                    reason=str(err),
                    operator=operator,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"unbind finished: success={success_count}, skipped={skipped_count}, failed={failed_count}"
            )
        )
