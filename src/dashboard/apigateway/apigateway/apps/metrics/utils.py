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
import math

from apigateway.utils.time import SmartTimeRange


class MetricsSmartTimeRange(SmartTimeRange):
    def get_recommended_step(self) -> str:
        """根据 time_start, time_end，获取推荐的步长"""
        start, end = self.get_head_and_tail()

        return self._calculate_step(start, end)

    def _calculate_step(self, start: int, end: int) -> str:
        """
        :param start: 起始时间戳
        :param end: 结束时间戳
        :returns: 推荐步长

        step via the gap of query time
        1m  <- 1h
        5m  <- 6h
        10m <- 12h
        30m <- 24h
        1h  <- 72h
        3h  <- 7d
        12h <- >7d
        """
        step_options = ["1m", "5m", "10m", "30m", "1h", "3h", "12h"]

        gap_minutes = math.ceil((end - start) / 60)
        if gap_minutes <= 60:
            index = 0
        elif gap_minutes <= 360:
            index = 1
        elif gap_minutes <= 720:
            index = 2
        elif gap_minutes <= 1440:
            index = 3
        elif gap_minutes <= 4320:
            index = 4
        elif gap_minutes <= 10080:
            index = 5
        else:
            index = 6

        return step_options[index]
