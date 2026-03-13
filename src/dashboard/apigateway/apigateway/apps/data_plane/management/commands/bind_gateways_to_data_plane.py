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
from apigateway.controller.constants import NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.tasks.syncing import rolling_update_release
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Gateway, Release, Stage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Bind gateways to one data plane and publish only to that data plane. 仅供灰度使用，不应该作为日常运维使用"

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

    def _bind_one_gateway(
        self,
        gateway: Gateway,
        data_plane: DataPlane,
        operator: str,
        dry_run: bool,
        audit_writer: AuditWriter,
        audit_log_common_args: dict,
    ) -> str:
        binding_exists = GatewayDataPlaneBinding.objects.filter(
            gateway_id=gateway.id,
            data_plane_id=data_plane.id,
        ).exists()
        if binding_exists:
            audit_writer.write(
                result="skipped",
                reason="already_bound",
                **audit_log_common_args,
            )
            return "skipped"

        if dry_run:
            self.stdout.write(f"[DRY RUN] would bind gateway={gateway.name} to data_plane={data_plane.name}")
            return "success"

        GatewayDataPlaneBinding.objects.bind_gateway_to_data_plane(
            gateway=gateway,
            data_plane=data_plane,
            created_by=operator,
        )

        # only trigger if gateway is active and stage is active and release is not None
        if not gateway.is_active:
            audit_writer.write(
                result="success",
                reason="gateway_is_not_active: no trigger publish",
                **audit_log_common_args,
            )
            self.stdout.write(f"gateway={gateway.name} is not active, skipped publish")
            return "success"

        stages = Stage.objects.filter(gateway=gateway, status=StageStatusEnum.ACTIVE.value).all()
        if not stages:
            audit_writer.write(
                result="success",
                reason="no_active_stage: no trigger publish",
                **audit_log_common_args,
            )
            self.stdout.write(f"gateway={gateway.name} has no active stage, skipped publish")
            return "success"

        # NOTE: each gateway-stage has only one release, so we can trigger one by one, to make sure all success
        publish_to_all_stages_success = True
        for stage in stages:
            release = Release.objects.filter(gateway_id=gateway.id, stage_id=stage.id).first()
            if not release:
                self.stdout.write(f"gateway={gateway.name} stage={stage.name} has no release, skipped publish")
                # NOTE: should not mark as failed, it ok for some stage has no release
                continue

            # NOTE: publish_id is NO_NEED_REPORT_EVENT_PUBLISH_ID, would not change the stage status
            # only update release.updated_time and release.updated_by
            ok = rolling_update_release(
                gateway_id=gateway.id,
                publish_id=NO_NEED_REPORT_EVENT_PUBLISH_ID,
                release_id=release.id,
                data_plane_id=data_plane.id,
            )
            if not ok:
                self.stdout.write(
                    f"failed to publish to gateway={gateway.name} stage={stage.name}, mark as failed and skipped publish"
                )
                publish_to_all_stages_success = False
                break

        if not publish_to_all_stages_success:
            GatewayDataPlaneBinding.objects.unbind_gateway_from_data_plane(
                gateway_id=gateway.id,
                data_plane_id=data_plane.id,
            )
            audit_writer.write(
                result="failed",
                reason="publish_to_all_stages_failed",
                **audit_log_common_args,
            )
            return "failed"

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
        operator = options["operator"]
        dry_run = options["dry_run"]
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
            gateway = gateway_by_name[gateway_name]

            audit_log_common_args = {
                "action": "bind_gateway_to_data_plane",
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
                result = self._bind_one_gateway(
                    gateway,
                    data_plane=data_plane,
                    operator=operator,
                    dry_run=dry_run,
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
                    "failed to bind gateway to data plane: gateway=%s, data_plane=%s",
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
                f"bind finished: success={success_count}, skipped={skipped_count}, failed={failed_count}"
            )
        )
