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
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext as _

from apigateway.apps.metrics.models import StatisticsGatewayRequestByDay
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Release, ResourceVersion, Stage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--template",
            type=str,
            required=True,
            help="环境访问地址（匹配参数：{gateway_id}/{stage_name}）",
        )

        parser.add_argument(
            "--resource-count",
            type=int,
            required=True,
            help="资源数量",
        )

        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="查询范围（单位：天）",
        )

    def handle(self, *args, **options):
        template = options["template"]
        days = options["days"]
        resource_count = options["resource_count"]

        # 获取环境已发布的记录
        release_version_ids = set()
        gateway_stage_map = defaultdict(list)
        for obj in Release.objects.filter(
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
        ).select_related("gateway", "stage", "resource_version"):
            release_version_ids.add(obj.resource_version_id)
            gateway_stage_map[obj.gateway.id].append(obj.stage.name)

        # 获取符合资源数量要求的网关 ID
        resource_version_gateway_ids = [
            obj.gateway.id
            for obj in ResourceVersion.objects.filter(id__in=release_version_ids).select_related("gateway")
            if len(obj.data) >= resource_count
        ]

        # 获取符合条件的网关和环境
        gateway_stage_set = {
            (gateway_id, stage_name)
            for gateway_id in resource_version_gateway_ids
            for stage_name in gateway_stage_map.get(gateway_id, [])
        }

        # 查询指定时间段内有访问记录的网关和环境
        start_time = timezone.now() + datetime.timedelta(days=-days)
        statistics_gateway_stage_set = set(
            StatisticsGatewayRequestByDay.objects.filter(
                gateway_id__in={gs[0] for gs in gateway_stage_set},
                stage_name__in={gs[1] for gs in gateway_stage_set},
                start_time__gte=start_time,
            ).values_list("gateway_id", "stage_name")
        )

        # 获取无访问记录的网关和环境
        export_gateway_stage_set = gateway_stage_set - statistics_gateway_stage_set
        data = [
            {
                "gateway_name": obj.gateway.name,
                "stage_name": obj.name,
                "desc": obj.description or "",
                "access_url": template.format(gateway_id=obj.gateway.id, stage_name=obj.name),
                "deactivated": "否" if obj.is_active else "是",
                "maintainers": obj.gateway._maintainers,
                "created_by": obj.created_by,
                "created_time": obj.created_time,
                "options": "",
            }
            for gateway_id, stage_name in export_gateway_stage_set
            for obj in Stage.objects.filter(
                gateway_id=gateway_id,
                name=stage_name,
            ).select_related("gateway")
        ]
        data = sorted(data, key=lambda x: x["gateway_name"])

        if not data:
            self.stdout.write("无数据导出")
            return

        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.export_to_csv(data, f"gateway_inactive_statistics_by_stage_{days}_{now}")

    def export_to_csv(self, data, filename):
        full_path = f"{filename}.csv"

        with open(full_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            headers = [
                "gateway_name",
                "stage_name",
                "desc",
                "access_url",
                "deactivated",
                "maintainers",
                "created_by",
                "created_time",
                "options",
            ]
            header_row = {
                "gateway_name": _("网关名称"),
                "stage_name": _("环境名称"),
                "desc": _("环境描述"),
                "access_url": _("环境访问地址"),
                "deactivated": _("环境是否已停用"),
                "maintainers": _("网关负责人"),
                "created_by": _("环境发布人"),
                "created_time": _("环境发布时间"),
                "options": _("操作选项"),
            }
            io_csv = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
            io_csv.writerow(header_row)
            io_csv.writerows(data)

        self.stdout.write(self.style.SUCCESS(f"已导出到 {full_path} (共 {len(data)} 条)"))
