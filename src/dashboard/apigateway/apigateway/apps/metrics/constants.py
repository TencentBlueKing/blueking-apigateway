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
from blue_krill.data_types.enum import EnumField, StructuredEnum


class MetricsRangeEnum(StructuredEnum):
    REQUESTS = EnumField("requests")
    NON_20X_STATUS = EnumField("non_20x_status")
    APP_REQUESTS = EnumField("app_requests")
    RESOURCE_REQUESTS = EnumField("resource_requests")
    RESPONSE_TIME_90TH = EnumField("response_time_90th")
    INGRESS = EnumField("ingress")
    EGRESS = EnumField("egress")


class MetricsInstantEnum(StructuredEnum):
    REQUESTS_TOTAL = EnumField("requests_total")
    HEALTH_RATE = EnumField("health_rate")


class MetricsRequestEnum(StructuredEnum):
    REQUESTS_TOTAL = EnumField("requests_total", label="请求总数")
    REQUESTS_FAILED_TOTAL = EnumField("requests_failed_total", label="请求失败总数")


class MetricsRequestTimeDimensionEnum(StructuredEnum):
    DAY = EnumField("day", label="按天统计")
    WEEK = EnumField("week", label="按周统计")
    MONTH = EnumField("month", label="按月统计")
