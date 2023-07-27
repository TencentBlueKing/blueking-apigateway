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
import itertools
import operator

from django.db import models


class StatisticsAPIRequestManager(models.Manager):
    def filter_and_aggregate_by_gateway(self, start_time, end_time):
        """
        过滤，并根据网关聚合数据
        """
        queryset = (
            self.filter(start_time__range=(start_time, end_time))
            .values("api_id", "total_count", "failed_count")
            .order_by("api_id")
        )
        api_request_groups = itertools.groupby(queryset, key=operator.itemgetter("api_id"))

        api_request_data = {}
        for api_id, group in api_request_groups:
            total_count = 0
            failed_count = 0
            for record in group:
                total_count += record["total_count"]
                failed_count += record["failed_count"]

            api_request_data[api_id] = {
                "api_id": api_id,
                "total_count": total_count,
                "failed_count": failed_count,
            }

        return api_request_data


class StatisticsAppRequestManager(models.Manager):
    def filter_app_and_aggregate_by_gateway(self, start_time, end_time):
        """
        过滤出蓝鲸应用，并根据网关聚合数据
        """
        # DISTINCT ON fields 依赖 mysql 版本，当前 mysql 版本不支持
        queryset = (
            self.filter(start_time__range=(start_time, end_time)).values("api_id", "bk_app_code").order_by("api_id")
        )
        app_request_groups = itertools.groupby(queryset, key=operator.itemgetter("api_id"))

        app_request_data = {}
        for api_id, group in app_request_groups:
            bk_app_code_set = set()
            for record in group:
                bk_app_code_set.add(record["bk_app_code"])

            app_request_data[api_id] = {
                "api_id": api_id,
                "bk_app_code_list": list(bk_app_code_set),
            }

        return app_request_data
