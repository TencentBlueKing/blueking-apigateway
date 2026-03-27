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
from django.db.models import Sum
from django.utils import timezone

from apigateway.apps.metrics.models import StatisticsAppRequestByDay
from apigateway.core.models import Gateway, Resource


class Command(BaseCommand):
    help = "导出指定网关最近 N 天内各应用对各资源的请求统计数据"

    BATCH_SIZE = 2000

    def add_arguments(self, parser):
        parser.add_argument(
            "--gateway-name",
            type=str,
            required=True,
            help="网关名称",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="查询范围（单位：天，默认 365）",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="",
            help="输出文件路径（默认自动生成）",
        )

    def handle(self, *args, **options):
        gateway_name = options["gateway_name"]
        days = options["days"]
        output = options["output"]

        try:
            gateway = Gateway.objects.get(name=gateway_name)
        except Gateway.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"网关 '{gateway_name}' 不存在"))
            return

        gateway_id = gateway.id
        self.stdout.write(f"网关: {gateway_name} (ID: {gateway_id})")

        start_time = timezone.now() - datetime.timedelta(days=days)

        resource_name_map = dict(
            Resource.objects.filter(gateway_id=gateway_id).values_list("id", "name")
        )
        self.stdout.write(f"共有 {len(resource_name_map)} 个资源")

        self.stdout.write("正在聚合统计数据，数据量较大请耐心等待...")

        queryset = (
            StatisticsAppRequestByDay.objects.filter(
                gateway_id=gateway_id,
                start_time__gte=start_time,
            )
            .values("bk_app_code", "resource_id")
            .annotate(
                total=Sum("total_count"),
                failed=Sum("failed_count"),
            )
            .order_by("-total")
        )

        if not output:
            now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            output = f"app_request_stats_{gateway_name}_{days}d_{now}.csv"

        count = 0
        with open(output, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["bk_app_code", "resource_name", "total_count", "failed_count"])

            for row in queryset.iterator(chunk_size=self.BATCH_SIZE):
                resource_name = resource_name_map.get(row["resource_id"], f"unknown({row['resource_id']})")
                writer.writerow([
                    row["bk_app_code"],
                    resource_name,
                    row["total"],
                    row["failed"],
                ])
                count += 1
                if count % 5000 == 0:
                    self.stdout.write(f"  已写入 {count} 行...")

        self.stdout.write(self.style.SUCCESS(f"已导出到 {output} (共 {count} 条)"))
