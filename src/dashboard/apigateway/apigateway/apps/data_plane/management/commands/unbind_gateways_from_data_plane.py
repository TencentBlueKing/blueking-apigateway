#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import logging

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apigateway.apps.data_plane.management.commands.gateway_data_plane_command_utils import (
    AuditWriter,
    parse_comma_separated_names,
    parse_gateway_names,
    parse_names_from_file,
)
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.tasks.syncing import revoke_release
from apigateway.core.models import Gateway, Release

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Unbind gateways from one data plane after synchronous revoke"

    def add_arguments(self, parser: CommandParser) -> None:
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
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
        parser.add_argument(
            "--force-unbind-last",
            action="store_true",
            help="Allow unbinding the last data plane binding of a gateway",
        )

    def _unbind_one_gateway(
        self,
        gateway: Gateway,
        data_plane: DataPlane,
        dry_run: bool,
        force_unbind_last: bool,
        audit_writer: AuditWriter,
        audit_log_common_args: dict,
    ) -> str:
        binding = GatewayDataPlaneBinding.objects.filter(
            gateway_id=gateway.id,
            data_plane_id=data_plane.id,
        ).first()
        if not binding:
            audit_writer.write(
                result="skipped",
                reason="binding_not_found",
                **audit_log_common_args,
            )
            return "skipped"

        bound_data_planes = GatewayDataPlaneBinding.objects.get_gateway_data_planes(gateway.id)
        if len(bound_data_planes) <= 1 and not force_unbind_last:
            audit_writer.write(
                result="failed",
                reason="last_binding_guard_blocked",
                **audit_log_common_args,
            )
            return "failed"

        if dry_run:
            self.stdout.write(f"[DRY RUN] would unbind gateway={gateway.name} from data_plane={data_plane.name}")
            return "success"

        # would try to revoke release at that data_plane, maybe a release list
        releases = Release.objects.filter(gateway_id=gateway.id).all()
        revoked = True
        for release in releases:
            ok = revoke_release(
                release_id=release.id,
                publish_id=DELETE_PUBLISH_ID,
                data_plane_id=data_plane.id,
                update_stage_status=False,
            )
            if not ok:
                revoked = False
                # we want to revoke as more as possible
                continue

        if not revoked:
            audit_writer.write(
                result="failed",
                reason="revoke_failed",
                **audit_log_common_args,
            )
            return "failed"

        GatewayDataPlaneBinding.objects.unbind_gateway_from_data_plane(
            gateway_id=gateway.id,
            data_plane_id=data_plane.id,
        )
        audit_writer.write(
            result="success",
            **audit_log_common_args,
        )
        return "success"

    def handle(self, *args, **options) -> None:
        gateway_names = parse_gateway_names(options["gateway_names"], options["gateway_names_file"])
        skip_gateway_names = set(parse_comma_separated_names(options["skip_gateway_names"]))
        skip_gateway_names.update(parse_names_from_file(options["skip_gateway_names_file"], "skip gateway names file"))
        data_plane_name = options["data_plane_name"].strip()
        dry_run = options["dry_run"]
        force_unbind_last = options["force_unbind_last"]
        audit_writer = AuditWriter(self.stdout, options["log_file"])

        if not data_plane_name:
            raise CommandError("data_plane_name should not be empty")

        data_plane = DataPlane.objects.filter(name=data_plane_name).first()
        if not data_plane:
            raise CommandError(f"data plane not found: {data_plane_name}")

        gateways = Gateway.objects.filter(name__in=gateway_names)
        gateway_by_name = {gateway.name: gateway for gateway in gateways}

        # maybe some gateway from args not in the database, so we need to print them out
        not_found_gateway_names = set(gateway_names) - set(gateway_by_name.keys())
        if not_found_gateway_names:
            failed_message = f"some gateway names not found in the database: {not_found_gateway_names}"
            self.stdout.write(self.style.WARNING(failed_message))
            raise CommandError(failed_message)

        success_count = 0
        skipped_count = 0
        failed_count = 0

        for gateway_name in gateway_names:
            # we already checked the gateway exists in the database, so we can safely get it
            gateway = gateway_by_name[gateway_name]

            audit_log_common_args = {
                "action": "unbind_gateway_from_data_plane",
                "gateway_id": gateway.id,
                "gateway_name": gateway.name,
                "data_plane_id": data_plane.id,
                "data_plane_name": data_plane.name,
            }

            if gateway_name in skip_gateway_names:
                skipped_count += 1
                audit_writer.write(
                    result="skipped",
                    reason="skipped_by_argument",
                    **audit_log_common_args,
                )
                continue

            try:
                result = self._unbind_one_gateway(
                    gateway,
                    data_plane=data_plane,
                    dry_run=dry_run,
                    force_unbind_last=force_unbind_last,
                    audit_writer=audit_writer,
                    audit_log_common_args=audit_log_common_args,
                )
                if result == "success":
                    success_count += 1
                elif result == "skipped":
                    skipped_count += 1
                else:
                    failed_count += 1
            except Exception as err:  # pylint: disable=broad-except
                failed_count += 1
                logger.exception(
                    "failed to unbind gateway from data plane: gateway=%s, data_plane=%s",
                    gateway_name,
                    data_plane_name,
                )
                audit_writer.write(
                    result="failed",
                    reason=str(err),
                    **audit_log_common_args,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"unbind finished: success={success_count}, skipped={skipped_count}, failed={failed_count}"
            )
        )
