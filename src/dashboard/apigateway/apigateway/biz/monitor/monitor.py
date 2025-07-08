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
from collections import defaultdict

from rest_framework.fields import DateTimeField

from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.biz.gateway import GatewayHandler


class MonitorHandler:
    @staticmethod
    def statistics_gateway_alarm_record(username, time_start, time_end):
        """
        统计网关下，各策略的告警信息
        """
        # 1. get current user's gateways
        # NOTE: here we don't need to get the username's tenant_id,
        # while the username/tenant_id is verified before create gateway
        gateways = GatewayHandler.list_gateways_by_user(username)
        gateway_id_map = {g.id: g for g in gateways}

        # 2. annotate alarm-record by strategy
        strategies = AlarmStrategy.objects.annotate_alarm_record_by_strategy(
            gateway_ids=gateway_id_map.keys(),
            time_start=time_start,
            time_end=time_end,
        )
        # 3. annotate alarm-record by gateway
        gateway_alarmrecord_count_map = AlarmStrategy.objects.annotate_alarm_record_by_gateway(
            gateway_ids=gateway_id_map.keys(),
            time_start=time_start,
            time_end=time_end,
        )

        # 4. summary
        latest_alarm_record_ids = [s.latest_alarm_record_id for s in strategies]
        alarm_record_id_map = AlarmRecord.objects.in_bulk(latest_alarm_record_ids)

        gateway_summary_map = defaultdict(list)
        for strategy in strategies:
            alarm_record = alarm_record_id_map[strategy.latest_alarm_record_id]
            gateway_summary_map[strategy.gateway_id].append(
                {
                    "id": strategy.id,
                    "name": strategy.name,
                    "alarm_record_count": strategy.alarm_record_count,
                    "latest_alarm_record": {
                        "id": alarm_record.id,
                        "message": alarm_record.message,
                        "created_time": DateTimeField().to_representation(alarm_record.created_time),
                    },
                }
            )

        gateway_summary = []
        for gateway_id, summary in gateway_summary_map.items():
            gateway = gateway_id_map[gateway_id]
            gateway_summary.append(
                {
                    "gateway": {
                        "id": gateway.id,
                        "name": gateway.name,
                    },
                    # 因为一个告警记录可能属于多条策略，因此将策略告警记录数量相加，并不等于网关告警记录数量
                    "alarm_record_count": gateway_alarmrecord_count_map.get(gateway.id, 0),
                    "strategy_summary": summary,
                }
            )
        return sorted(gateway_summary, key=lambda x: x["gateway"]["name"])
