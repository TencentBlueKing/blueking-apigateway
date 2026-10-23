# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusEnum, ReleaseHistoryStatusEnum
from apigateway.core.models import Gateway, PublishEvent, ReleaseHistory, Stage
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock


class Command(BaseCommand):
    help = "Recover expired publishes with missing events. Preview by default; does not republish configuration."

    def add_arguments(self, parser):
        gateway = parser.add_mutually_exclusive_group(required=True)
        gateway.add_argument("--gateway-id", type=int, help="Gateway ID.")
        gateway.add_argument("--gateway_name", "--gateawy_name", dest="gateway_name", help="Exact gateway name.")
        parser.add_argument(
            "--stage",
            "--stage_name",
            dest="stage_name",
            help="Exact stage name; defaults to all stages of the gateway.",
        )
        parser.add_argument("--apply", action="store_true", help="Write recovery events; otherwise only preview.")
        parser.add_argument(
            "--operator", default="", help="Recovery operator (required with --apply, max 32 characters)."
        )
        parser.add_argument("--reason", default="", help="Recovery reason (required with --apply).")

    def handle(self, *args, **options):
        operator = options["operator"].strip()
        reason = options["reason"].strip()
        if options["apply"] and (not operator or len(operator) > 32 or not reason):
            raise CommandError("--apply requires --operator (1-32 characters) and a non-empty --reason.")

        gateway = self._get_gateway(options["gateway_id"], options["gateway_name"])
        stages = Stage.objects.filter(gateway=gateway).order_by("id")
        if options["stage_name"] is not None:
            if not options["stage_name"].strip():
                raise CommandError("Stage name must not be empty.")
            stages = stages.filter(name=options["stage_name"])
            if not stages.exists():
                raise CommandError("Stage does not belong to the gateway.")

        for stage in stages:
            # Match the stage status query and recovery SQL: only MAX(id) for
            # the whole stage, including histories with a legacy NULL data plane.
            history = ReleaseHistory.objects.filter(stage=stage).order_by("-id").first()
            if history is None:
                self.stdout.write(f"gateway={gateway.id} stage={stage.name} skipped: no publish history")
                continue
            if history.gateway_id != gateway.id:
                outcome = "skipped: publish history does not belong to the gateway"
            elif options["apply"]:
                try:
                    with (
                        Lock(
                            f"{gateway.id}_{stage.id}",
                            timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                            try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
                        ),
                        transaction.atomic(),
                    ):
                        outcome = self._recover(history, operator, reason)
                except LockTimeout as err:
                    raise CommandError(
                        f"Could not acquire publish lock for gateway={gateway.id} stage={stage.name}"
                    ) from err
            else:
                outcome = self._skip_reason(history) or "would_recover"
            self.stdout.write(
                f"gateway={gateway.id} gateway_name={gateway.name} stage={stage.name} "
                f"data_plane={history.data_plane_id} publish_id={history.id} {outcome}"
            )

    @staticmethod
    def _get_gateway(gateway_id: int | None, gateway_name: str | None) -> Gateway:
        # call_command keyword options also need validation; they can bypass
        # argparse's mutually exclusive group checks.
        if (gateway_id is None) == (gateway_name is None):
            raise CommandError("Specify exactly one of --gateway-id and --gateway_name.")
        if gateway_name is not None:
            if not gateway_name.strip():
                raise CommandError("Gateway name must not be empty.")
            gateway = Gateway.objects.filter(name=gateway_name).first()
        else:
            gateway = Gateway.objects.filter(pk=gateway_id).first()
        if gateway is None:
            raise CommandError("Gateway does not exist.")
        if gateway.is_programmable:
            raise CommandError("Programmable gateways must be recovered through their deployment workflow.")
        return gateway

    @staticmethod
    def _skip_reason(history: ReleaseHistory) -> str:
        if PublishEvent.objects.filter(publish_id=history.id).exists():
            return "skipped: publish events exist"
        if history.get_status(None) != ReleaseHistoryStatusEnum.FAILURE.value:
            return "skipped: publish has not timed out or its creation time is unknown"
        return ""

    def _recover(self, history: ReleaseHistory, operator: str, reason: str) -> str:
        # Recheck the selected publish and its events after acquiring the same
        # lock as the release API. Never terminate a newer or observed publish.
        current = ReleaseHistory.objects.select_for_update().filter(stage_id=history.stage_id).order_by("-id").first()
        if current is None or current.id != history.id or current.gateway_id != history.gateway_id:
            return "skipped: latest publish changed"
        skip_reason = self._skip_reason(current)
        if skip_reason:
            return skip_reason

        name = PublishEventNameTypeEnum.VALIDATE_CONFIGURATION
        PublishEvent.objects.create(
            gateway_id=current.gateway_id,
            stage_id=current.stage_id,
            publish=current,
            name=name.value,
            step=PublishEventNameTypeEnum.get_event_step(name.value),
            status=PublishEventStatusEnum.FAILURE.value,
            detail={
                "err_msg": "Manual recovery: publish events missing after timeout; original deployment result unknown.",
                "reason": reason,
            },
            created_by=operator,
            updated_by=operator,
        )
        return "recovered: failure event recorded"
