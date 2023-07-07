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
import datetime
import math
from typing import Union

import arrow
from dateutil.tz import tzutc
from django.conf import settings
from django.utils import timezone

ARROW_FORMAT_WITH_TZ = "YYYY-MM-DD HH:mm:ssZ"


def now_str():
    """
    :return: local format str
    """
    return arrow.now("local").format(ARROW_FORMAT_WITH_TZ)


def aware_time(value):
    if not timezone.is_aware(value):
        value = timezone.make_aware(value)
    return value


def utctime(value, *args, **kwargs):
    """
    Convert value to arrow utc time
    :param value: datetime object, tz time str, arrow object
    :return: a arrow object with utc tzinfo
    """
    if isinstance(value, datetime.datetime):
        value = aware_time(value)
    return arrow.get(value, *args, **kwargs).to("utc")


def format(value, fmt=ARROW_FORMAT_WITH_TZ, *args, **kwargs):
    """
    :param value: timestamp, utc time str, arrow object, datetime object
    :return: local format str
    """
    if isinstance(value, datetime.datetime):
        value = aware_time(value)
    return arrow.get(value, *args, **kwargs).to("local").format(fmt)


def now_datetime():
    """
    :return datetime: now datetime
    """
    return arrow.utcnow().datetime


def now_timestamp():
    """
    :return: int, current timestamp
    """
    return arrow.utcnow().int_timestamp


def timestamp(value, *args, **kwargs):
    """
    :param value: utc time str, arrow object, datetime object
    :return: int, the timestamp
    """
    if isinstance(value, datetime.datetime):
        value = aware_time(value)
    return arrow.get(value, *args, **kwargs).int_timestamp


def far_away_future():
    if settings.USE_TZ:
        return datetime.datetime(year=2050, month=1, day=1, tzinfo=timezone.utc)
    else:
        return datetime.datetime(year=2050, month=1, day=1)


def to_datetime_from_now(days: Union[int, None] = None) -> datetime.datetime:
    result = timezone.now()
    if days is not None:
        result += datetime.timedelta(days=days)

    return result


def to_seconds(days: Union[int, None] = None) -> int:
    result = 0
    if days is not None:
        result += days * 24 * 3600

    return result


def convert_epoch_millis_to_second(value):
    """
    将 ES 中的时间戳转换为秒
    """
    return math.ceil(value / 1000.0)


def convert_second_to_epoch_millis(value):
    return value * 1000 if value is not None else None


def calculate_interval(time_start, time_end, wide=True):
    """
    :param int time_start: second timestamp
    :param int time_end: second timestamp

    interval via the gap of query time
    fit for graph width >= 40%
    1  s  <-   60s
    10 s  <-   10m
    30 s  <-   30m
    1  m  <-   1h  - 60
    5  m  <-   6h  - 360
    10 m  <-   12h - 720
    30 m  <-   24h - 1440
    1  h  <-   72h - 4320
    3  h  <-   7d  - 10080
    12 h  <-   >7d
    """
    gap_seconds = time_end - time_start
    return calculate_gap_seconds_interval(gap_seconds, wide)


def calculate_gap_seconds_interval(gap_seconds, wide=True):
    gap_min = math.ceil(gap_seconds / 60)
    if wide:
        interval_options = ["1s", "10s", "30s", "1m", "5m", "10m", "30m", "1h", "3h", "1d"]
    else:
        interval_options = ["10s", "30s", "1m", "5m", "10m", "30m", "1h", "3h", "6h", "1d"]

    if gap_min <= 1:
        index = 0
    elif gap_min <= 10:
        index = 1
    elif gap_min <= 30:
        index = 2
    elif gap_min <= 60:
        index = 3
    elif gap_min <= 360:
        index = 4
    elif gap_min <= 720:
        index = 5
    elif gap_min <= 1440:
        index = 6
    elif gap_min <= 4320:
        index = 7
    elif gap_min <= 10080:
        index = 8
    else:
        index = 9
    return interval_options[index]


class NeverExpiresTime:
    # 永久有效期，使用2100.01.01 00:00:00 的unix time作为永久有效期的表示，时间戳为：4102444800
    time = datetime.datetime(2100, 1, 1, 0, 0, tzinfo=tzutc())

    @classmethod
    def is_never_expired(cls, value):
        return value >= NeverExpiresTime.time


class SmartTimeRange:
    def __init__(self, time_start=None, time_end=None, time_range=None):
        """
        time_start+time_end, time_range 至少一组有效
        """
        self.time_range = time_range
        self.time_start = time_start
        self.time_end = time_end

    def get_head_and_tail(self):
        if self.time_start and self.time_end:
            return (self.time_start, self.time_end)

        now = now_timestamp()
        return (now - self.time_range, now)

    def get_interval(self):
        time_start, time_end = self.get_head_and_tail()
        return calculate_interval(time_start, time_end)
