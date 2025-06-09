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
from cachetools import TTLCache, cached
from django.db import models
from django.db.models import Count, Max, Q

from apigateway.common.constants import CACHE_MAXSIZE, CACHE_TIME_5_MINUTES


class AlarmRecordManager(models.Manager):
    def update_alarm(self, id, gateway=None, status=None, comment=None, message=None, alarm_strategies=None):
        data = {}
        if gateway is not None:
            data["gateway"] = gateway

        if status is not None:
            data["status"] = status

        if comment is not None:
            data["comment"] = comment

        if message is not None:
            data["message"] = message

        if data:
            self.filter(id=id).update(**data)

        if alarm_strategies is not None:
            self.get(id=id).alarm_strategies.set(alarm_strategies)


class AlarmFilterConfigManager(models.Manager):
    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TIME_5_MINUTES))
    def get_filter_config(self, alarm_type):
        configs = (x.config for x in self.filter(alarm_type=alarm_type))
        return list(filter(None, configs))


class AlarmStrategyManager(models.Manager):
    def filter_alarm_strategy(self, gateway, gateway_label_id=None, keyword=None, order_by=None, fuzzy=True):
        queryset = self.filter(gateway=gateway)

        if keyword and fuzzy:
            queryset = queryset.filter(name__contains=keyword)

        if gateway_label_id is not None:
            queryset = queryset.filter(api_labels__id=gateway_label_id)

        if order_by is not None:
            queryset = queryset.order_by(order_by)

        return queryset.distinct()

    def annotate_alarm_record_by_strategy(self, gateway_ids, time_start=None, time_end=None):
        """
        统计指定的告警策略下，告警记录的数量，及最新的告警记录ID
        """
        alarm_record_count = self._get_alarm_record_count_object(time_start, time_end)
        return (
            self.filter(gateway_id__in=gateway_ids)
            .annotate(alarm_record_count=alarm_record_count, latest_alarm_record_id=Max("alarmrecord"))
            .filter(alarm_record_count__gt=0)
        )

    def annotate_alarm_record_by_gateway(self, gateway_ids, time_start=None, time_end=None):
        """
        统计指定网关下，告警记录的数量
        """
        alarm_record_count = self._get_alarm_record_count_object(time_start, time_end)
        return dict(
            self.filter(gateway_id__in=gateway_ids)
            .values_list("gateway_id")
            .annotate(alarm_record_count=alarm_record_count)
        )

    def _get_alarm_record_count_object(self, time_start=None, time_end=None):
        """
        获取监控告警记录的统计 Count 对象
        """
        if time_start and time_end:
            return Count(
                "alarmrecord",
                distinct=True,
                filter=Q(alarmrecord__created_time__range=(time_start, time_end)),
            )

        return Count("alarmrecord", distinct=True)
