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
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from apigateway.apps.metrics.models import StatisticsAppRequestByDay, StatisticsGatewayRequestByDay
from apigateway.core.models import Gateway, Resource, Stage
from apigateway.utils.time import utctime


class Command(BaseCommand):
    def handle(self, *args, **options):
        dates = self._get_dates()
        gateways = Gateway.objects.all()
        total = gateways.count()

        self.stdout.write(f"开始为{total}个网关生成假数据...")

        for idx, gateway in enumerate(gateways, 1):
            self.stdout.write(f"\r处理进度: {idx}/{total}", ending="")
            self.stdout.flush()

            gateway_request_data = []
            app_request_data = []

            resource_ids = Resource.objects.filter(gateway=gateway).values_list("id", flat=True)
            if not resource_ids:
                continue

            for date in dates:
                for stage in Stage.objects.filter(gateway=gateway):
                    gateway_request_data.append(
                        StatisticsGatewayRequestByDay(
                            gateway_id=gateway.id,
                            stage_name=stage.name,
                            resource_id=random.choice(resource_ids),
                            total_count=random.randint(0, 1000),
                            failed_count=random.randint(0, 100),
                            total_msecs=random.randint(60, 600),
                            start_time=date,
                            end_time=date,
                        )
                    )

                    app_request_data.append(
                        StatisticsAppRequestByDay(
                            gateway_id=gateway.id,
                            stage_name=stage.name,
                            resource_id=random.choice(resource_ids),
                            bk_app_code=random.choice(["app1", "app2", "app3"]),
                            total_count=random.randint(0, 1000),
                            failed_count=random.randint(0, 100),
                            total_msecs=random.randint(60, 600),
                            start_time=date,
                            end_time=date,
                        )
                    )

            StatisticsGatewayRequestByDay.objects.bulk_create(gateway_request_data, batch_size=100)
            StatisticsAppRequestByDay.objects.bulk_create(app_request_data, batch_size=100)

        self.stdout.write("\n假数据生成完成!")

    def _get_dates(self):
        now = datetime.now()
        return [utctime(int((now - timedelta(days=i)).timestamp())).datetime for i in range(30)]
