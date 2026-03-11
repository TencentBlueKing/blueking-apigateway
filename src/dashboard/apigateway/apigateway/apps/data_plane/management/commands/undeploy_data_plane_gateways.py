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

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.data_plane.management.commands.gateway_data_plane_command_utils import (
    AuditWriter,
    parse_comma_separated_names,
    parse_names_from_file,
)
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.tasks.syncing import revoke_release

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Undeploy (revoke) gateways from a specific data plane without changing stage status or bindings"

    def add_arguments(self, parser):
        parser.add_argument("--data-plane-name", type=str, required=True, help="Target data plane name")

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--all",
            action="store_true",
            dest="undeploy_all",
            help="Undeploy all gateways bound to the data plane",
        )
        group.add_argument("--gateway-names", type=str, default="", help="Gateway names to undeploy, comma separated")

        parser.add_argument(
            "--skip-gateway-names",
            type=str,
            default="",
            help="Gateway names to skip, comma separated",
        )
        parser.add_argument(
            "--skip-gateway-names-file",
            type=str,
            default="",
            help="File with gateway names to skip, one per line",
        )
        parser.add_argument("--log-file", type=str, required=True, help="Audit log file path")
        parser.add_argument("--operator", type=str, default="system", help="Operator username")
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")

    def _get_bound_gateways(self, data_plane):
        bindings = GatewayDataPlaneBinding.objects.filter(data_plane=data_plane).select_related("gateway")
        return {b.gateway.name: b.gateway for b in bindings}

    def _undeploy_one_gateway(self, gateway, data_plane, release_model, dry_run, audit_writer, operator):
        if dry_run:
            self.stdout.write(f"[DRY RUN] would undeploy gateway={gateway.name} from data_plane={data_plane.name}")
            return "success"

        releases = release_model.objects.filter(gateway_id=gateway.id).all()
        if not releases:
            audit_writer.write(
                action="undeploy_data_plane_gateway",
                result="success",
                gateway_name=gateway.name,
                gateway_id=gateway.id,
                data_plane_name=data_plane.name,
                data_plane_id=data_plane.id,
                reason="no_releases",
                operator=operator,
            )
            self.stdout.write(f"gateway={gateway.name} has no releases, nothing to revoke")
            return "success"

        all_revoked = True
        for release in releases:
            ok = revoke_release(
                release_id=release.id,
                publish_id=DELETE_PUBLISH_ID,
                data_plane_id=data_plane.id,
                update_stage_status=False,
            )
            if not ok:
                all_revoked = False
                self.stdout.write(
                    f"failed to revoke release={release.id} for gateway={gateway.name}, "
                    f"mark as failed and skip remaining"
                )
                break

        if not all_revoked:
            audit_writer.write(
                action="undeploy_data_plane_gateway",
                result="failed",
                gateway_name=gateway.name,
                gateway_id=gateway.id,
                data_plane_name=data_plane.name,
                data_plane_id=data_plane.id,
                reason="revoke_failed",
                operator=operator,
            )
            return "failed"

        audit_writer.write(
            action="undeploy_data_plane_gateway",
            result="success",
            gateway_name=gateway.name,
            gateway_id=gateway.id,
            data_plane_name=data_plane.name,
            data_plane_id=data_plane.id,
            operator=operator,
        )
        return "success"

    def handle(self, *args, **options):  # noqa: C901, PLR0912, PLR0915
        data_plane_name = options["data_plane_name"].strip()
        undeploy_all = options["undeploy_all"]
        gateway_names_raw = options["gateway_names"]
        operator = options["operator"]
        dry_run = options["dry_run"]
        audit_writer = AuditWriter(self.stdout, options["log_file"])
        release_model = apps.get_model("core", "Release")

        skip_gateway_names = set(parse_comma_separated_names(options["skip_gateway_names"]))
        skip_gateway_names.update(parse_names_from_file(options["skip_gateway_names_file"], "skip gateway names file"))

        if not data_plane_name:
            raise CommandError("data_plane_name should not be empty")

        data_plane = DataPlane.objects.filter(name=data_plane_name).first()
        if not data_plane:
            raise CommandError(f"data plane not found: {data_plane_name}")

        bound_gateway_by_name = self._get_bound_gateways(data_plane)

        if undeploy_all:
            gateway_names = list(bound_gateway_by_name.keys())
        else:
            gateway_names = parse_comma_separated_names(gateway_names_raw)
            if not gateway_names:
                raise CommandError("no valid gateway names provided via --gateway-names")

        if not gateway_names:
            raise CommandError(f"no gateways bound to data plane: {data_plane_name}")

        self.stdout.write(
            f"undeploying {len(gateway_names)} gateway(s) from data_plane={data_plane_name} "
            f"(skip={len(skip_gateway_names)}, dry_run={dry_run})"
        )

        success_count = 0
        skipped_count = 0
        failed_count = 0

        for gateway_name in gateway_names:
            if gateway_name in skip_gateway_names:
                skipped_count += 1
                audit_writer.write(
                    action="undeploy_data_plane_gateway",
                    result="skipped",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="skipped_by_argument",
                    operator=operator,
                )
                continue

            gateway = bound_gateway_by_name.get(gateway_name)
            if not gateway:
                failed_count += 1
                audit_writer.write(
                    action="undeploy_data_plane_gateway",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="gateway_not_bound_to_data_plane",
                    operator=operator,
                )
                continue

            try:
                result = self._undeploy_one_gateway(
                    gateway,
                    data_plane=data_plane,
                    release_model=release_model,
                    dry_run=dry_run,
                    audit_writer=audit_writer,
                    operator=operator,
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
                    "failed to undeploy gateway from data plane: gateway=%s, data_plane=%s",
                    gateway_name,
                    data_plane_name,
                )
                audit_writer.write(
                    action="undeploy_data_plane_gateway",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                    reason=str(err),
                    operator=operator,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"undeploy finished: success={success_count}, skipped={skipped_count}, failed={failed_count}"
            )
        )
