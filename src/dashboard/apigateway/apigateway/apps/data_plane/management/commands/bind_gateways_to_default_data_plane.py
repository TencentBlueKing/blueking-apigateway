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

from django.core.management.base import BaseCommand

from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Bind all gateways without data plane binding to the default data plane."""

    help = "Bind all gateways that are not bound to any data plane to the default data plane"

    def handle(self, *args, **options):
        self.stdout.write("Binding gateways to default data plane...")

        # Get default data plane
        default_data_plane = DataPlane.objects.get_default()
        if not default_data_plane:
            self.stdout.write(self.style.WARNING("Default data plane not found. Run init_default_data_plane first."))
            return

        # Get all gateways without data plane binding
        unbound_gateways = GatewayDataPlaneBinding.objects.get_gateways_without_binding()

        if not unbound_gateways:
            self.stdout.write(self.style.SUCCESS("All gateways are already bound to a data plane."))
            return

        self.stdout.write(f"Found {len(unbound_gateways)} gateways without data plane binding.")

        # Bind each gateway to the default data plane
        bound_count = 0
        for gateway in unbound_gateways:
            try:
                GatewayDataPlaneBinding.objects.bind_gateway_to_data_plane(
                    gateway=gateway,
                    data_plane=default_data_plane,
                    created_by="system",
                )
                bound_count += 1
                self.stdout.write(f"  Bound gateway '{gateway.name}' (id={gateway.id}) to default data plane")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Failed to bind gateway '{gateway.name}' (id={gateway.id}): {e}")
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully bound {bound_count} gateways to the default data plane."))
