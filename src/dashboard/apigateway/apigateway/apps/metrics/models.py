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
from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.common.mixins.models import TimestampedModelMixin


class StatisticsModelMixin(models.Model):
    total_count = models.BigIntegerField(default=0)
    failed_count = models.BigIntegerField(default=0)
    total_msecs = models.BigIntegerField(default=0)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)

    class Meta:
        abstract = True


class StatisticsGatewayRequest(StatisticsModelMixin, TimestampedModelMixin):
    """
    网关请求统计
    """

    gateway_id = models.IntegerField(db_index=True, db_column="api_id")
    stage_name = models.CharField(max_length=64)
    resource_id = models.IntegerField()

    class Meta:
        abstract = True


class StatisticsAppRequest(StatisticsModelMixin, TimestampedModelMixin):
    """
    应用请求统计
    """

    gateway_id = models.IntegerField(db_index=True, db_column="api_id")
    bk_app_code = models.CharField(max_length=32)
    stage_name = models.CharField(max_length=64)
    resource_id = models.IntegerField()

    class Meta:
        abstract = True


# TODO: 支持按小时统计
# - 可以展示更细粒度的请求量信息
# - 可以支持按时区展示统计数据，按天的统计数据，无法支持按时区展示
# - 注意：按小时统计，数据量较大，建议保留较短时间数据，如 3 个月，定期清理过期数据
# class StatisticsAppRequestByHour(StatisticsAppRequest):

#     class Meta:
#         verbose_name = '应用请求统计 (按小时)'
#         verbose_name_plural = '应用请求统计 (按小时)'
#         db_table = 'metrics_stats_app_request_by_hour'


class StatisticsGatewayRequestByDay(StatisticsGatewayRequest):
    class Meta:
        verbose_name = _("网关请求统计(按天)")
        verbose_name_plural = _("网关请求统计(按天)")
        db_table = "metrics_stats_api_request_by_day"


class StatisticsAppRequestByDay(StatisticsAppRequest):
    class Meta:
        verbose_name = _("应用请求统计(按天)")
        verbose_name_plural = _("应用请求统计(按天)")
        db_table = "metrics_stats_app_request_by_day"
