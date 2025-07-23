# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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

from django.core.management.base import BaseCommand, CommandError

from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import PublishSourceEnum, StageStatusEnum
from apigateway.core.models import Gateway, Stage


class Command(BaseCommand):
    help = "Deactivate stage by name."

    def add_arguments(self, parser):
        parser.add_argument(
            "--gateway",
            type=str,
            required=True,
            help="Gateway name.",
        )
        parser.add_argument(
            "--stage",
            type=str,
            required=True,
            help="Stage name.",
        )

    def handle(self, *args, **options):
        gateway_name = options["gateway"]
        stage_name = options["stage"]

        if not gateway_name:
            raise CommandError("No gateway name provided.")
        if not stage_name:
            raise CommandError("No stage name provided.")

        gateway = Gateway.objects.filter(name=gateway_name).first()
        if not gateway:
            self.stdout.write(self.style.ERROR("No valid gateway found. Exiting."))
            return

        stage = Stage.objects.filter(gateway=gateway, name=stage_name).first()
        if not stage:
            self.stdout.write(self.style.ERROR("No valid stage found. Exiting."))
            return

        if stage.is_active:
            # Trigger publish event for stage deactivation
            trigger_gateway_publish(
                PublishSourceEnum.STAGE_DISABLE,
                "system_deactivated",
                stage.gateway_id,
                stage.id,
                is_sync=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Deactivated gateway id={gateway.id}, name={gateway.name}, stage={stage.name}")
            )
            stage.status = StageStatusEnum.INACTIVE.value
            stage.save()
