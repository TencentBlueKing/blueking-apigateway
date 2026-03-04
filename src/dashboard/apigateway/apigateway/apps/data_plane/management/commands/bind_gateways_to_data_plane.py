import logging
from importlib import import_module

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
    help = "Bind gateways to one data plane and publish only to that data plane"

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

    def handle(self, *args, **options):
        gateway_names = parse_gateway_names(options["gateway_names"], options["gateway_names_file"])
        skip_gateway_names = set(parse_comma_separated_names(options["skip_gateway_names"]))
        skip_gateway_names.update(parse_names_from_file(options["skip_gateway_names_file"], "skip gateway names file"))
        data_plane_name = options["data_plane_name"].strip()
        operator = options["operator"]
        audit_writer = AuditWriter(self.stdout, options["log_file"])
        gateway_model = apps.get_model("core", "Gateway")
        constants_module = import_module("apigateway.core.constants")
        publish_module = import_module("apigateway.controller.publisher.publish")
        publish_source_enum = constants_module.PublishSourceEnum
        trigger_gateway_publish = publish_module.trigger_gateway_publish

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
                    action="bind_gateway_to_data_plane",
                    result="skipped",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="skipped_by_argument",
                )
                continue

            gateway = gateway_by_name.get(gateway_name)
            if not gateway:
                failed_count += 1
                audit_writer.write(
                    action="bind_gateway_to_data_plane",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="gateway_not_found",
                )
                continue

            try:
                binding_exists = GatewayDataPlaneBinding.objects.filter(
                    gateway_id=gateway.id,
                    data_plane_id=data_plane.id,
                ).exists()
                if binding_exists:
                    skipped_count += 1
                    audit_writer.write(
                        action="bind_gateway_to_data_plane",
                        result="skipped",
                        gateway_name=gateway.name,
                        gateway_id=gateway.id,
                        data_plane_name=data_plane.name,
                        data_plane_id=data_plane.id,
                        reason="already_bound",
                    )
                    continue

                GatewayDataPlaneBinding.objects.bind_gateway_to_data_plane(
                    gateway=gateway,
                    data_plane=data_plane,
                    created_by=operator,
                )

                trigger_gateway_publish(
                    publish_source_enum.CLI_SYNC,
                    author=operator,
                    gateway_id=gateway.id,
                    is_sync=True,
                    target_data_plane_ids=[data_plane.id],
                )

                success_count += 1
                audit_writer.write(
                    action="bind_gateway_to_data_plane",
                    result="success",
                    gateway_name=gateway.name,
                    gateway_id=gateway.id,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                )
            except Exception as err:  # pylint: disable=broad-except
                failed_count += 1
                logger.exception(
                    "failed to bind gateway to data plane: gateway=%s, data_plane=%s",
                    gateway_name,
                    data_plane_name,
                )
                audit_writer.write(
                    action="bind_gateway_to_data_plane",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                    reason=str(err),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"bind finished: success={success_count}, skipped={skipped_count}, failed={failed_count}"
            )
        )
