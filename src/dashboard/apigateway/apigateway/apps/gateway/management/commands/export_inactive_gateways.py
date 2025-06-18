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
import csv
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext as _

from apigateway.apps.metrics.models import StatisticsGatewayRequestByDay
from apigateway.core.models import Gateway


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--template",
            type=str,
            required=True,
            help="网关访问地址",
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

        gateways = Gateway.objects.all()
        gateway_ids = list(gateways.values_list("id", flat=True))
        start_time = timezone.now() + datetime.timedelta(days=-days)

        exclude_gateway_ids = list(
            StatisticsGatewayRequestByDay.objects.filter(
                gateway_id__in=gateway_ids,
                start_time__gte=start_time,
            )
            .values_list("gateway_id", flat=True)
            .distinct()
        )

        data = [
            {
                "name": obj.name,
                "desc": obj.description or "",
                "access_url": template.format(gateway_id=obj.id),
                "deactivated": "否" if obj.is_active else "是",
                "maintainers": obj._maintainers,
                "created_by": obj.created_by,
                "created_time": obj.created_time,
                "options": "",
            }
            for obj in gateways.exclude(id__in=exclude_gateway_ids).order_by("name")
        ]

        if not data:
            self.stdout.write("无数据导出")
            return

        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.export_to_csv(data, f"gateway_inactive_statistics_{days}_{now}")

    def export_to_csv(self, data, filename):
        full_path = f"{filename}.csv"

        with open(full_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            headers = [
                "name",
                "desc",
                "access_url",
                "deactivated",
                "maintainers",
                "created_by",
                "created_time",
                "options",
            ]
            header_row = {
                "name": _("网关名"),
                "desc": _("网关描述"),
                "access_url": _("网关访问地址"),
                "deactivated": _("是否已停用"),
                "maintainers": _("网关负责人"),
                "created_by": _("网关创建人"),
                "created_time": _("创建时间"),
                "options": _("操作选项"),
            }
            io_csv = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
            io_csv.writerow(header_row)
            io_csv.writerows(data)

        self.stdout.write(self.style.SUCCESS(f"已导出到 {full_path} (共 {len(data)} 条)"))
