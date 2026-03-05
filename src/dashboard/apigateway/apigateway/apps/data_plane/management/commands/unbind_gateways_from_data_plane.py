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
from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.tasks.syncing import revoke_release

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
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
        parser.add_argument(
            "--force-unbind-last",
            action="store_true",
            help="Allow unbinding the last data plane binding of a gateway",
        )

    def _revoke_gateway_releases(
        self, gateway: Any, data_plane_id: int, release_model: Any, revoke_release: Any, delete_publish_id: int
    ) -> bool:
        releases = release_model.objects.filter(gateway_id=gateway.id).all()
        for release in releases:
            ok = revoke_release(release_id=release.id, publish_id=delete_publish_id, data_plane_id=data_plane_id)
            if not ok:
                return False
        return True

    def _handle_skip(self, audit_writer: AuditWriter, gateway_name: str, data_plane: DataPlane, operator: str):
        audit_writer.write(
            action="unbind_gateway_from_data_plane",
            result="skipped",
            gateway_name=gateway_name,
            data_plane_name=data_plane.name,
            reason="skipped_by_argument",
            operator=operator,
        )

    def _handle_gateway_not_found(
        self, audit_writer: AuditWriter, gateway_name: str, data_plane: DataPlane, operator: str
    ):
        audit_writer.write(
            action="unbind_gateway_from_data_plane",
            result="failed",
            gateway_name=gateway_name,
            data_plane_name=data_plane.name,
            reason="gateway_not_found",
            operator=operator,
        )

    def _unbind_one_gateway(
        self,
        gateway: Any,
        data_plane: DataPlane,
        operator: str,
        dry_run: bool,
        force_unbind_last: bool,
        release_model: Any,
        audit_writer: AuditWriter,
    ) -> str:
        binding = GatewayDataPlaneBinding.objects.filter(
            gateway_id=gateway.id,
            data_plane_id=data_plane.id,
        ).first()
        if not binding:
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
            return "skipped"

        bound_data_planes = GatewayDataPlaneBinding.objects.get_gateway_data_planes(gateway.id)
        if len(bound_data_planes) <= 1 and not force_unbind_last:
            audit_writer.write(
                action="unbind_gateway_from_data_plane",
                result="failed",
                gateway_name=gateway.name,
                gateway_id=gateway.id,
                data_plane_name=data_plane.name,
                data_plane_id=data_plane.id,
                reason="last_binding_guard_blocked",
                operator=operator,
            )
            return "failed"

        if dry_run:
            self.stdout.write(f"[DRY RUN] would unbind gateway={gateway.name} from data_plane={data_plane.name}")
            return "success"

        revoked = self._revoke_gateway_releases(
            gateway,
            data_plane.id,
            release_model=release_model,
            revoke_release=revoke_release,
            delete_publish_id=DELETE_PUBLISH_ID,
        )
        if not revoked:
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
            return "failed"

        GatewayDataPlaneBinding.objects.unbind_gateway_from_data_plane(
            gateway_id=gateway.id,
            data_plane_id=data_plane.id,
        )
        audit_writer.write(
            action="unbind_gateway_from_data_plane",
            result="success",
            gateway_name=gateway.name,
            gateway_id=gateway.id,
            data_plane_name=data_plane.name,
            data_plane_id=data_plane.id,
            operator=operator,
        )
        return "success"

    def handle(self, *args, **options):
        gateway_names = parse_gateway_names(options["gateway_names"], options["gateway_names_file"])
        skip_gateway_names = set(parse_comma_separated_names(options["skip_gateway_names"]))
        skip_gateway_names.update(parse_names_from_file(options["skip_gateway_names_file"], "skip gateway names file"))
        data_plane_name = options["data_plane_name"].strip()
        operator = options["operator"]
        dry_run = options["dry_run"]
        force_unbind_last = options["force_unbind_last"]
        audit_writer = AuditWriter(self.stdout, options["log_file"])
        gateway_model = apps.get_model("core", "Gateway")
        release_model = apps.get_model("core", "Release")

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
                self._handle_skip(audit_writer, gateway_name, data_plane, operator)
                continue

            gateway = gateway_by_name.get(gateway_name)
            if not gateway:
                failed_count += 1
                self._handle_gateway_not_found(audit_writer, gateway_name, data_plane, operator)
                continue

            try:
                result = self._unbind_one_gateway(
                    gateway,
                    data_plane=data_plane,
                    operator=operator,
                    dry_run=dry_run,
                    force_unbind_last=force_unbind_last,
                    release_model=release_model,
                    audit_writer=audit_writer,
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
