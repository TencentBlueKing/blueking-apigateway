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
import time

from django.conf import settings
from rest_framework.views import APIView

from apigateway.apps.esb.bkcore.models import RealTimelineEvent
from apigateway.apps.esb.status.es_client import get_search_es_client
from apigateway.apps.esb.status.utils import get_system_basic_info, str_percentage, str_to_seconds
from apigateway.utils.responses import OKJsonResponse


class SysAllSummaryView(APIView):
    """Summary data for third-party system"""

    def get(self, request):
        time_since = request.GET.get("time_since") or "24h"
        result = es_get_system_stats(time_since)
        [complement_summary(d) for d in result]

        # 添加每个系统的基本信息
        system_names = [x["system_name"] for x in result]
        system_basic_info = get_system_basic_info(system_names)
        for info in result:
            info["basic_info"] = system_basic_info[info["system_name"]]

        return OKJsonResponse("OK", data=result)


class SysEventsTimeline(APIView):
    """Get timeline data for all system events"""

    time_interval = "5m"
    time_interval_seconds = str_to_seconds(time_interval)

    def get(self, request):  # noqa
        time_since = request.GET.get("time_since") or "12h"

        # 首先从数据库中查询已经存在的 RealTimelineEvent 减小 ES 计算范围
        ts_started_from = time.time() - str_to_seconds(time_since)
        db_events = RealTimelineEvent.objects.filter(ts_happened_at__gte=ts_started_from).order_by("-ts_happened_at")
        last_db_ts_happened_at = db_events[0].ts_happened_at if db_events else ts_started_from
        db_events = [e.as_dict() for e in db_events]

        es_client = get_search_es_client()
        data = es_client.get_sys_events_timeline(
            last_db_ts_happened_at,
            self.time_interval_seconds,
            self.time_interval,
        )

        system_aggregations_data = self._parse_aggregations_data(data)
        init_system_in_dropped = self._get_init_system_in_dropped(db_events)
        events = self._analyze_system_aggregations_data(system_aggregations_data, init_system_in_dropped)

        # 按照时间从新到旧排序
        events.sort(key=lambda x: (x["mts"], x["system_name"]), reverse=True)

        # 将实时计算的事件插入数据库
        self._save_real_timeline_events(events)

        # 和数据库中的 events 组合起来
        events.extend(db_events)

        for event in events:
            event["mts_end"] = event["mts"] + self.time_interval_seconds * 1000

        events = self._add_system_info(events)
        return OKJsonResponse("OK", data=events)

    def _parse_aggregations_data(self, data):
        if "aggregations" not in data:
            return {}

        ret = {}
        for system_data in data["aggregations"]["systems"]["buckets"]:
            system_name = system_data["key"]
            result = []
            for bucket_data in system_data["requests_over_time"]["buckets"]:
                if not bucket_data["doc_count"]:
                    continue

                # 二次处理服务可用率等信息
                summary = {
                    "mts": bucket_data["key"],
                    "requests": {
                        "count": bucket_data["doc_count"],
                        "error_count": bucket_data["error_count"]["doc_count"],
                    },
                }
                summary["rate_availability"] = {
                    "value": 1 - (summary["requests"]["error_count"] / float(summary["requests"]["count"]))
                }
                summary["rate_availability"]["value_str"] = str_percentage(summary["rate_availability"]["value"])
                result.append(summary)
            ret[system_name] = result

        return ret

    def _get_init_system_in_dropped(self, db_events):
        init_system_in_dropped = {}
        # 遍历 db_events 来确定 in_availability_dropped 的初始值
        # None 表示没有在故障进程中，时间戳表示上一次发生故障的时间
        for db_event in reversed(db_events):
            if db_event["type"] == "availability_dropped":
                init_system_in_dropped[db_event["system_name"]] = int(db_event["mts"])
            elif db_event["type"] == "availability_restored":
                init_system_in_dropped[db_event["system_name"]] = None

        return init_system_in_dropped

    def _analyze_system_aggregations_data(self, system_aggregations_data, init_system_in_dropped):
        # 分析数据序列产生 events
        events = []
        for system_name, data in system_aggregations_data.items():
            in_availability_dropped = init_system_in_dropped.get(system_name, None)
            for i, time_piece in enumerate(data):
                # 可用率突然降低
                if time_piece["rate_availability"]["value"] < 1:
                    # 对于这段时间总请求数大于 5 的才当做可用率下降，否则当做普通错误
                    if in_availability_dropped:
                        continue
                    elif (
                        time_piece["requests"]["count"] > 5
                        and time_piece["requests"]["error_count"] > 1
                        and (i == 0 or data[i - 1]["rate_availability"]["value"] == 1)
                    ):
                        in_availability_dropped = time_piece["mts"]
                        event_type = "availability_dropped"
                    else:
                        event_type = "errors_occurred"

                # 可用率从低点恢复
                elif time_piece["rate_availability"]["value"] == 1 and in_availability_dropped:
                    event_type = "availability_restored"
                    time_piece["msecs_avai_dropped"] = time_piece["mts"] - in_availability_dropped
                    in_availability_dropped = None
                else:
                    continue

                events.append(
                    {"type": event_type, "system_name": system_name, "mts": time_piece["mts"], "data": time_piece}
                )

        return events

    def _save_real_timeline_events(self, events):
        """将实时计算的事件插入数据库"""
        for live_event in events:
            key = dict(system_name=live_event["system_name"], ts_happened_at=live_event["mts"] / 1000)
            # 判断事件不存在，插入事件
            # 最近一分钟的事件不要插入，因为这个数据会被更新
            if (
                not RealTimelineEvent.objects.filter(**key).exists()
                and live_event["mts"] < (time.time() - self.time_interval_seconds) * 1000
            ):
                RealTimelineEvent(
                    board=settings.ESB_DEFAULT_BOARD, type=live_event["type"], data=live_event["data"], **key
                ).save()

    def _add_system_info(self, events):
        """通过 system_name 来完善系统基本信息"""
        system_names = [x["system_name"] for x in events]
        system_basic_info = get_system_basic_info(system_names)
        for info in events:
            info["basic_info"] = system_basic_info[info["system_name"]]
        return events


class SysUnstableSystemsView(APIView):
    """Get recent unstable systems"""

    def get(self, request):
        time_since = request.GET.get("time_since") or "10m"

        result = es_get_system_stats(time_since)

        # 筛选出有问题的系统摘要
        [complement_summary(d) for d in result]
        ret = [x for x in result if x["unstable"]]
        return OKJsonResponse("OK", data=ret)


class SysSummaryView(APIView):
    """Summary data for third-party system"""

    def get(self, request, system_name):
        mts_start = request.GET.get("mts_start")
        mts_end = request.GET.get("mts_end")
        time_since = request.GET.get("time_since", "24h")
        result = es_get_system_stats(time_since, system_name=system_name, mts_start=mts_start, mts_end=mts_end)

        if result:
            data = result[0]
            complement_summary(data)
        else:
            data = {
                "requests": {"count": 0, "count_str": "0", "error_count": 0},
                "avg_resp_time": {"value": 0, "value_str": "0"},
                "perc95_resp_time": {"value": 0, "value_str": "0"},
                "rate_availability": {"value": 1, "value_str": "0.00"},
            }

        # 获取系统基本信息
        system_basic_info = get_system_basic_info([system_name])
        data["basic_info"] = system_basic_info[system_name]
        return OKJsonResponse("OK", data=data)


class SysDateHistogramView(APIView):
    """date_histogram data for third-party system"""

    def get(self, request, system_name):
        mts_start = request.GET.get("mts_start")
        mts_end = request.GET.get("mts_end", int(time.time() * 1000))
        time_interval = request.GET.get("time_interval", "1m")

        es_client = get_search_es_client()
        data = es_client.get_sys_date_histogram(
            mts_start,
            mts_end,
            system_name,
            time_interval,
        )

        result = []
        for bucket_data in data["aggregations"]["systems"]["buckets"]:
            summary = process_bucket_data(bucket_data)
            # 最近的时间序列数据
            serial_data = bucket_data["requests_over_time"]["buckets"]
            summary["requests"]["data"] = [(x["key"], x["doc_count"]) for x in serial_data]
            summary["avg_resp_time"]["data"] = [(x["key"], x["avg_resp_time"]["value"]) for x in serial_data]
            summary["perc95_resp_time"]["data"] = [
                (x["key"], x["resp_time_outlier"]["values"]["95.0"]) for x in serial_data
            ]
            summary["perc95_resp_time"]["data"] = [
                (key, value if value != "NaN" else None) for key, value in summary["perc95_resp_time"]["data"]
            ]
            summary["rate_availability"]["data"] = [
                (
                    x["key"],
                    100 * (1 - (x["error_count"]["doc_count"] / float(x["doc_count"])))
                    if x["doc_count"] != 0
                    else 100,
                )
                for x in serial_data
            ]
            result.append(summary)
        # 为方便js中判定data为空，无数据时，设值为None
        return OKJsonResponse("OK", data=result[0] if result else None)


class SysDetailsGroupByView(APIView):
    """Perc95 resp time data for third-party system"""

    def get(self, request, system_name):
        mts_start = request.GET.get("mts_start")
        mts_end = request.GET.get("mts_end") or int(time.time() * 1000)
        time_since = request.GET.get("time_since") or "10m"
        group_by = request.GET.get("group_by", "req_url")
        order = request.GET.get("order", "time_desc")
        size = request.GET.get("size") or 20

        es_client = get_search_es_client()
        data = es_client.get_sys_details_group_by(
            mts_start,
            mts_end,
            time_since,
            system_name,
            group_by,
        )
        result = []
        for bucket_data in data["aggregations"]["systems"]["buckets"]:
            summary = process_bucket_data(bucket_data, key_name=group_by)
            result.append(summary)

        # 对结果进行排序
        if order == "time_desc":
            result.sort(key=lambda x: x["perc95_resp_time"]["value"], reverse=True)
        elif order == "availability_asc":
            result.sort(key=lambda x: (x["rate_availability"]["value"], -x["requests"]["count"]))
        elif order == "requests_desc":
            result.sort(key=lambda x: x["requests"]["count"], reverse=True)
        return OKJsonResponse("OK", data=result[:size])


class SysErrorsView(APIView):
    """查询某个运营系统错误详情"""

    def get(self, request, system_name):
        url = request.GET.get("url", "")
        app_code = request.GET.get("app_code", "")
        component_name = request.GET.get("component_name", "")
        size = request.GET.get("size") or 200
        mts_start = request.GET.get("mts_start")
        mts_end = request.GET.get("mts_end")

        es_client = get_search_es_client()
        data = es_client.get_sys_errors(mts_start, mts_end, system_name, url, app_code, component_name, size)

        data_list = []
        for d in data["hits"]["hits"]:
            value = d["_source"]
            value["timestamp"] = d["sort"][0]
            data_list.append(value)

        return OKJsonResponse(
            "OK",
            data={
                "data": {
                    "data_list": data_list,
                },
                "result": True,
            },
        )


def es_get_system_stats(time_since=None, system_name=None, mts_start=None, mts_end=None):
    es_client = get_search_es_client()
    data = es_client.get_system_stats(
        time_since=time_since,
        system_name=system_name,
        mts_start=mts_start,
        mts_end=mts_end,
    )
    result = []
    if "aggregations" in data:
        for bucket_data in data["aggregations"]["systems"]["buckets"]:
            result.append(process_bucket_data(bucket_data))

    # 可用率最低，响应时间越慢的系统将会被放在最前面
    result.sort(key=lambda x: (x["rate_availability"]["value"], -x["perc95_resp_time"]["value"]))
    return result


def process_bucket_data(bucket_data, key_name="system_name"):
    """二次处理ES查询出的bucket_data"""
    try:
        avg_resp_time_value = int(bucket_data["avg_resp_time"]["value"])
    except Exception:
        avg_resp_time_value = 0
    try:
        resp_time_outlier_95_value = int(bucket_data["resp_time_outlier"]["values"]["95.0"])
    except Exception:
        resp_time_outlier_95_value = 0

    summary = {
        key_name: bucket_data["key"],
        "requests": {
            "count": bucket_data["doc_count"],
            "count_str": "{:,}".format(bucket_data["doc_count"]),
            "error_count": bucket_data["error_count"]["doc_count"],
        },
        "avg_resp_time": {"value": avg_resp_time_value, "value_str": avg_resp_time_value},
        "perc95_resp_time": {"value": resp_time_outlier_95_value, "value_str": resp_time_outlier_95_value},
    }
    summary["rate_availability"] = {
        "value": 1 - (summary["requests"]["error_count"] / float(summary["requests"]["count"]))
    }
    summary["rate_availability"]["value_str"] = str_percentage(summary["rate_availability"]["value"])
    return summary


def complement_summary(summary):
    """为查询出来的系统摘要信息补充更多内容，比如添加上 『是否响应速度慢』等内容

    :param dict summary: 系统摘要信息
    """
    d = summary
    d["warn_fields"] = {}
    d["unstable"] = False
    if d["rate_availability"]["value"] < 1:
        d["warn_fields"]["low_availability"] = True
        d["unstable"] = True
    if d["perc95_resp_time"]["value"] > 5000:
        d["warn_fields"]["slow_response"] = True
        d["unstable"] = True
