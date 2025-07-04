# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from apigateway.biz.gateway import GatewayHandler
from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import GatewayStatusEnum, PublishSourceEnum
from apigateway.core.models import Gateway


class Command(BaseCommand):
    help = "Deactivate or remove gateways by name."

    def add_arguments(self, parser):
        parser.add_argument(
            "--gateways",
            type=str,
            required=True,
            help="Gateway names, separated by comma.",
        )
        parser.add_argument(
            "--deactivate",
            action="store_true",
            help="Deactivate all stages and set gateway status to inactive.",
        )
        parser.add_argument(
            "--remove",
            action="store_true",
            help="Remove the gateway after deactivation.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done, but do not make changes.",
        )

    def handle(self, *args, **options):  # noqa: C901, PLR0912
        gateway_names = [name.strip() for name in options["gateways"].split(",") if name.strip()]
        do_deactivate = options["deactivate"]
        do_remove = options["remove"]
        dry_run = options["dry_run"]

        if not gateway_names:
            raise CommandError("No gateway names provided.")
        if do_deactivate and do_remove:
            raise CommandError("Only one of --deactivate or --remove can be specified.")
        if not (do_deactivate or do_remove):
            raise CommandError("You must specify either --deactivate or --remove.")

        gateways = Gateway.objects.filter(name__in=gateway_names)
        found_names = set(gateways.values_list("name", flat=True))
        not_found = [name for name in gateway_names if name not in found_names]

        for name in not_found:
            self.stdout.write(self.style.WARNING(f"Gateway not found: {name}"))

        if not gateways:
            self.stdout.write(self.style.ERROR("No valid gateways found. Exiting."))
            return

        # Show info
        for gw in gateways:
            maintainers = ", ".join(gw.maintainers)
            status = "ACTIVE" if gw.is_active else "INACTIVE"
            self.stdout.write(f"Gateway id={gw.id}, name={gw.name}, maintainers=[{maintainers}], status={status}")
            if do_remove:
                self.stdout.write(self.style.WARNING("  Would be REMOVED." if dry_run else "  Will be REMOVED."))
            else:
                self.stdout.write(
                    self.style.WARNING("  Would be DEACTIVATED." if dry_run else "  Will be DEACTIVATED.")
                )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run: no changes made."))
            return

        # Confirm
        confirm = input(_("Are you sure you want to continue? Type 'yes' to proceed: "))
        if confirm.strip().lower() != "yes":
            self.stdout.write(self.style.ERROR("Aborted by user."))
            return

        for gw in gateways:
            if do_deactivate or do_remove:  # noqa: SIM102
                if gw.is_active:
                    # Trigger publish event for gateway deactivation
                    trigger_gateway_publish(PublishSourceEnum.GATEWAY_DISABLE, "system_deactivate", gw.id)
                    self.stdout.write(self.style.SUCCESS(f"Deactivated gateway id={gw.id}, name={gw.name}"))
                    gw.status = GatewayStatusEnum.INACTIVE.value
                    gw.save()
            if do_remove:
                # Remove gateway from DB
                GatewayHandler.delete_gateway(gw.id)
                self.stdout.write(self.style.SUCCESS(f"Removed gateway id={gw.id}, name={gw.name}"))
