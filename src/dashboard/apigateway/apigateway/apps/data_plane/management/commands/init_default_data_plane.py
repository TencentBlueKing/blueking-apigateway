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

from django.conf import settings
from django.core.management.base import BaseCommand

from apigateway.apps.data_plane.constants import DEFAULT_DATA_PLANE_NAME, DataPlaneStatusEnum
from apigateway.apps.data_plane.models import DataPlane

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Initialize or update the default data plane from settings."""

    help = "Initialize or update the default data plane with ETCD configuration from settings"

    def handle(self, *args, **options):
        self.stdout.write("Initializing default data plane...")

        # Get ETCD config from settings
        etcd_config = getattr(settings, "ETCD_CONFIG", {})
        bk_api_url_tmpl = getattr(settings, "BK_API_URL_TMPL", "")

        # Try to get existing default data plane
        data_plane = DataPlane.objects.filter(name=DEFAULT_DATA_PLANE_NAME).first()

        if data_plane:
            # Update existing data plane (but don't update is_recommend)
            self.stdout.write(f"Updating existing default data plane (id={data_plane.id})...")
            data_plane.description = "The default data plane"
            data_plane.etcd_configs = etcd_config
            data_plane.bk_api_url_tmpl = bk_api_url_tmpl
            data_plane.status = DataPlaneStatusEnum.ACTIVE.value
            data_plane.updated_by = "system"
            data_plane.save()
            self.stdout.write(self.style.SUCCESS(f"Default data plane updated successfully (id={data_plane.id})"))
        else:
            # Create new data plane
            self.stdout.write("Creating new default data plane...")
            data_plane = DataPlane(
                name=DEFAULT_DATA_PLANE_NAME,
                description="The default data plane",
                bk_api_url_tmpl=bk_api_url_tmpl,
                status=DataPlaneStatusEnum.ACTIVE.value,
                is_recommend=True,
                created_by="system",
                updated_by="system",
            )
            # Set etcd_configs using the property to encrypt
            data_plane.etcd_configs = etcd_config
            data_plane.save()
            self.stdout.write(self.style.SUCCESS(f"Default data plane created successfully (id={data_plane.id})"))
