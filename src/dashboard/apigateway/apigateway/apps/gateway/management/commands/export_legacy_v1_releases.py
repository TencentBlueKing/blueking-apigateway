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
import csv
import datetime

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from apigateway.core.constants import (
    GatewayStatusEnum,
    ResourceVersionSchemaEnum,
    StageStatusEnum,
)
from apigateway.core.models import Release


class Command(BaseCommand):
    help = "Export releases that use legacy V1 resource version schema"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default="",
            help="Output file path (defaults to auto-generated timestamped filename)",
        )

    def handle(self, *args, **options):
        output_path = options["output"]

        releases = Release.objects.filter(
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
            resource_version__schema_version=ResourceVersionSchemaEnum.V1.value,
        ).select_related("gateway", "stage", "resource_version")

        data = [
            {
                "gateway_id": release.gateway.id,
                "gateway_name": release.gateway.name,
                "gateway_maintainers": release.gateway._maintainers,
                "gateway_created_by": release.gateway.created_by,
                "gateway_created_time": release.gateway.created_time,
                "stage_name": release.stage.name,
                "resource_version_version": release.resource_version.version,
                "resource_version_schema_version": release.resource_version.schema_version,
                "resource_version_created_time": release.resource_version.created_time,
            }
            for release in releases.order_by("gateway__id", "stage__name")
        ]

        if not data:
            self.stdout.write("No data to export")
            return

        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = output_path if output_path else f"legacy_v1_releases_{now}.csv"

        self.export_to_csv(data, filename)

    def export_to_csv(self, data, filename):
        with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
            headers = [
                "gateway_id",
                "gateway_name",
                "gateway_maintainers",
                "gateway_created_by",
                "gateway_created_time",
                "stage_name",
                "resource_version_version",
                "resource_version_schema_version",
                "resource_version_created_time",
            ]
            header_row = {
                "gateway_id": _("网关ID"),
                "gateway_name": _("网关名称"),
                "gateway_maintainers": _("网关负责人"),
                "gateway_created_by": _("网关创建人"),
                "gateway_created_time": _("网关创建时间"),
                "stage_name": _("环境名称"),
                "resource_version_version": _("资源版本号"),
                "resource_version_schema_version": _("资源版本Schema"),
                "resource_version_created_time": _("资源版本创建时间"),
            }
            io_csv = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
            io_csv.writerow(header_row)
            io_csv.writerows(data)

        self.stdout.write(self.style.SUCCESS(f"Exported to {filename} (total {len(data)} records)"))
