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

from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.data_plane.management.commands.gateway_data_plane_command_utils import (
    AuditWriter,
    parse_comma_separated_names,
    parse_names_from_file,
)
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import PublishSourceEnum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deploy (publish) gateways bound to a specific data plane"

    def add_arguments(self, parser):
        parser.add_argument("--data-plane-name", type=str, required=True, help="Target data plane name")

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--all",
            action="store_true",
            dest="deploy_all",
            help="Deploy all gateways bound to the data plane",
        )
        group.add_argument("--gateway-names", type=str, default="", help="Gateway names to deploy, comma separated")

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

    def handle(self, *args, **options):
        data_plane_name = options["data_plane_name"].strip()
        deploy_all = options["deploy_all"]
        gateway_names_raw = options["gateway_names"]
        operator = options["operator"]
        dry_run = options["dry_run"]
        audit_writer = AuditWriter(self.stdout, options["log_file"])

        skip_gateway_names = set(parse_comma_separated_names(options["skip_gateway_names"]))
        skip_gateway_names.update(parse_names_from_file(options["skip_gateway_names_file"], "skip gateway names file"))

        if not data_plane_name:
            raise CommandError("data_plane_name should not be empty")

        data_plane = DataPlane.objects.filter(name=data_plane_name).first()
        if not data_plane:
            raise CommandError(f"data plane not found: {data_plane_name}")

        bound_gateway_by_name = self._get_bound_gateways(data_plane)

        if deploy_all:
            gateway_names = list(bound_gateway_by_name.keys())
        else:
            gateway_names = parse_comma_separated_names(gateway_names_raw)
            if not gateway_names:
                raise CommandError("no valid gateway names provided via --gateway-names")

        if not gateway_names:
            raise CommandError(f"no gateways bound to data plane: {data_plane_name}")

        self.stdout.write(
            f"deploying {len(gateway_names)} gateway(s) to data_plane={data_plane_name} "
            f"(skip={len(skip_gateway_names)}, dry_run={dry_run})"
        )

        success_count = 0
        skipped_count = 0
        failed_count = 0

        for gateway_name in gateway_names:
            if gateway_name in skip_gateway_names:
                skipped_count += 1
                audit_writer.write(
                    action="deploy_data_plane_gateway",
                    result="skipped",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="skipped_by_argument",
                )
                continue

            gateway = bound_gateway_by_name.get(gateway_name)
            if not gateway:
                failed_count += 1
                audit_writer.write(
                    action="deploy_data_plane_gateway",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    reason="gateway_not_bound_to_data_plane",
                )
                continue

            try:
                if dry_run:
                    success_count += 1
                    self.stdout.write(f"[DRY RUN] would deploy gateway={gateway.name} to data_plane={data_plane.name}")
                    continue

                # trigger_gateway_publish handles inactive gateway/stage gracefully:
                # - inactive gateways or stages are skipped with a warning
                # - gateways with no releases are treated as success (nothing to publish)
                publish_success = trigger_gateway_publish(
                    PublishSourceEnum.CLI_SYNC,
                    author=operator,
                    gateway_id=gateway.id,
                    is_sync=True,
                    target_data_plane_ids=[data_plane.id],
                )
                if not publish_success:
                    raise RuntimeError("publish failed")

                success_count += 1
                audit_writer.write(
                    action="deploy_data_plane_gateway",
                    result="success",
                    gateway_name=gateway.name,
                    gateway_id=gateway.id,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                )
            except Exception as err:  # pylint: disable=broad-except
                failed_count += 1
                logger.exception(
                    "failed to deploy gateway to data plane: gateway=%s, data_plane=%s",
                    gateway_name,
                    data_plane_name,
                )
                audit_writer.write(
                    action="deploy_data_plane_gateway",
                    result="failed",
                    gateway_name=gateway_name,
                    data_plane_name=data_plane.name,
                    data_plane_id=data_plane.id,
                    reason=str(err),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"deploy finished: success={success_count}, skipped={skipped_count}, failed={failed_count}"
            )
        )
