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

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apigateway.controller.tasks.oauth2_builtin import (
    BuiltinPermission,
    OAuth2BuiltinPermissionReconciler,
)
from apigateway.core.models import Gateway


def _format_permissions(permissions: frozenset[BuiltinPermission]) -> str:
    return ",".join(f"{app_code}:{resource_id}" for app_code, resource_id in sorted(permissions))


class Command(BaseCommand):
    help = "Report or repair OAuth2 built-in resource permissions for one gateway."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--gateway", required=True, help="Gateway name")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes; without this flag the command is dry-run",
        )

    def handle(self, *args, **options):
        gateway_name = options["gateway"]
        gateway = Gateway.objects.filter(name=gateway_name).first()
        if gateway is None:
            raise CommandError(f"gateway not found: {gateway_name}")

        result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(
            gateway,
            apply=options["apply"],
        )
        self.stdout.write(f"gateway={gateway.name}")
        for name in ("desired", "missing", "to_delete", "unchanged"):
            permissions = getattr(result, name)
            self.stdout.write(f"{name} count={len(permissions)} rows={_format_permissions(permissions)}")
        self.stdout.write(f"applied={str(result.applied).lower()}")
        self.stdout.write(f"deletion_blocked={str(result.deletion_blocked).lower()}")
        for blocker in result.blockers:
            self.stdout.write(
                "blocked "
                f"stage={blocker.stage_name}({blocker.stage_id}) "
                f"data_plane={blocker.data_plane_name}({blocker.data_plane_id}) "
                f"release_history={blocker.release_history_id} "
                f"status={blocker.status}"
            )
