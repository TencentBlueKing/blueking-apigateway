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
import csv
import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.models import Max
from django.utils import timezone

from apigateway.apps.metrics.models import StatisticsGatewayRequestByDay
from apigateway.core.models import Gateway, Resource


def parse_gateway_names(gateway_names: Iterable[str], names_file: Optional[str]) -> List[str]:
    names: List[str] = []
    seen: Set[str] = set()

    for raw_name in gateway_names:
        name = raw_name.strip()
        if not name or name in seen:
            continue
        names.append(name)
        seen.add(name)

    if names_file:
        path = Path(names_file)
        if not path.exists() or not path.is_file():
            raise CommandError(f"gateway names file does not exist: {names_file}")

        try:
            raw_items = path.read_text(encoding="utf-8").splitlines()
        except OSError as err:
            raise CommandError(f"failed to read gateway names file: {names_file}, error: {err}") from err

        for raw_item in raw_items:
            item = raw_item.strip()
            if not item or item in seen:
                continue
            names.append(item)
            seen.add(item)

    if not names:
        raise CommandError("no gateway names provided, use --gateway-names or --gateway-names-file")
    return names


class Command(BaseCommand):
    help = "统计指定网关过去 N 天内无请求记录的资源列表，按网关维度输出 CSV"

    CSV_HEADERS = [
        "resource_id",
        "resource_name",
        "method",
        "path",
        "created_time",
        "last_request_time",
    ]

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--gateway-names",
            nargs="*",
            default=[],
            help="网关名称列表，可传多个",
        )
        parser.add_argument(
            "--gateway-names-file",
            type=str,
            default="",
            help="网关名称文件路径，每行一个网关名",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="查询范围（单位：天，默认 30）",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=".",
            help="输出目录（默认当前目录）",
        )

    def handle(self, *args, **options) -> None:
        gateway_names = parse_gateway_names(options["gateway_names"], options["gateway_names_file"] or None)
        days = options["days"]
        if days <= 0:
            raise CommandError("--days must be greater than 0")

        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        start_time = timezone.now() - datetime.timedelta(days=days)
        now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        self.stdout.write(f"统计范围: 过去 {days} 天 (start_time >= {start_time.isoformat()})")
        self.stdout.write(f"待处理网关数: {len(gateway_names)}")

        for gateway_name in gateway_names:
            self._process_gateway(gateway_name, start_time, days, output_dir, now_str)

    def _process_gateway(
        self,
        gateway_name: str,
        start_time: datetime.datetime,
        days: int,
        output_dir: Path,
        now_str: str,
    ) -> None:
        try:
            gateway = Gateway.objects.get(name=gateway_name)
        except Gateway.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"网关 '{gateway_name}' 不存在，跳过"))
            return

        resources = list(
            Resource.objects.filter(gateway_id=gateway.id)
            .order_by("id")
            .values("id", "name", "method", "path", "created_time")
        )
        total_count = len(resources)
        if total_count == 0:
            self.stdout.write("")
            self.stdout.write(f"=== 网关: {gateway_name} (ID: {gateway.id}) ===")
            self.stdout.write("该网关下无资源")
            return

        active_resource_ids = set(
            StatisticsGatewayRequestByDay.objects.filter(
                gateway_id=gateway.id,
                start_time__gte=start_time,
            )
            .values_list("resource_id", flat=True)
            .distinct()
        )

        inactive_resources = [item for item in resources if item["id"] not in active_resource_ids]
        inactive_ids = [item["id"] for item in inactive_resources]
        last_request_map = self._get_last_request_time_map(gateway.id, inactive_ids)

        output_path = output_dir / f"inactive_resources_{gateway_name}_{days}d_{now_str}.csv"
        self._export_to_csv(output_path, inactive_resources, last_request_map)

        self.stdout.write("")
        self.stdout.write(f"=== 网关: {gateway_name} (ID: {gateway.id}) ===")
        self.stdout.write(f"资源总数: {total_count}")
        self.stdout.write(f"过去 {days} 天无请求记录的资源数: {len(inactive_resources)}")
        self.stdout.write(self.style.SUCCESS(f"已导出到 {output_path}"))

    def _get_last_request_time_map(self, gateway_id: int, resource_ids: List[int]) -> Dict[int, datetime.datetime]:
        if not resource_ids:
            return {}

        rows = (
            StatisticsGatewayRequestByDay.objects.filter(
                gateway_id=gateway_id,
                resource_id__in=resource_ids,
            )
            .values("resource_id")
            .annotate(last_request_time=Max("start_time"))
        )
        return {row["resource_id"]: row["last_request_time"] for row in rows}

    def _export_to_csv(
        self,
        output_path: Path,
        inactive_resources: List[dict],
        last_request_map: Dict[int, datetime.datetime],
    ) -> None:
        with output_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for resource in inactive_resources:
                last_request_time = last_request_map.get(resource["id"])
                writer.writerow(
                    {
                        "resource_id": resource["id"],
                        "resource_name": resource["name"] or "",
                        "method": resource["method"],
                        "path": resource["path"],
                        "created_time": self._format_datetime(resource["created_time"]),
                        "last_request_time": self._format_datetime(last_request_time),
                    }
                )

    @staticmethod
    def _format_datetime(value: Optional[datetime.datetime]) -> str:
        if not value:
            return ""
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%Y-%m-%d %H:%M:%S")
