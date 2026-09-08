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
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, F, OuterRef, Q
from django.db.models.functions import Trim

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.models import Gateway


class Command(BaseCommand):
    help = "检查切换网关 RBAC 前的 GatewayMember 数据"

    def handle(self, *args, **options):
        members = GatewayMember.objects.filter(gateway_id=OuterRef("pk"))
        administrators = members.filter(role=GatewayRoleEnum.ADMINISTRATOR.value)
        gateways = Gateway.objects.annotate(
            _has_member=Exists(members),
            _has_administrator=Exists(administrators),
        )

        empty_gateways = list(gateways.filter(_has_member=False).order_by("id").values_list("id", "name"))
        gateways_without_administrator = list(
            gateways.filter(_has_member=True, _has_administrator=False).order_by("id").values_list("id", "name")
        )
        invalid_members = list(
            GatewayMember.objects.exclude(role__in=GatewayRoleEnum.get_values())
            .order_by("gateway_id", "id")
            .values_list("id", "gateway_id", "username", "role")
        )
        invalid_username_members = list(
            GatewayMember.objects.annotate(_trimmed_username=Trim("username"))
            .filter(Q(_trimmed_username="") | ~Q(username=F("_trimmed_username")))
            .order_by("gateway_id", "id")
            .values_list("id", "gateway_id", "username")
        )

        failures = {
            "empty_gateways": empty_gateways,
            "gateways_without_administrator": gateways_without_administrator,
            "invalid_members": invalid_members,
            "invalid_username_members": invalid_username_members,
        }
        for name, records in failures.items():
            self.stdout.write(f"{name}: count={len(records)}, records={records}")

        if any(failures.values()):
            raise CommandError("GatewayMember 数据检查失败")

        self.stdout.write(self.style.SUCCESS("GatewayMember 数据检查通过"))
