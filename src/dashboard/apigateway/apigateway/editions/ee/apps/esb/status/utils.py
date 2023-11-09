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
import re

from apigateway.apps.esb.bkcore.models import ComponentSystem


def get_system_basic_info(system_names):
    """获取系统的基本信息"""
    system_objs = ComponentSystem.objects.filter(name__in=system_names)
    system_obj_map = {x.name: x for x in system_objs}
    system_basic_info = {}
    for system_name in system_names:
        system_obj = system_obj_map.get(system_name)
        if system_obj:
            system_basic_info[system_name] = {
                "name": system_obj.name,
                "description": system_obj.description,
                "maintainers": system_obj.maintainers,
            }
        else:
            system_basic_info[system_name] = {
                "name": system_name,
                "description": system_name,
                "maintainers": "",
            }

    return system_basic_info


def str_percentage(v):
    return truncate(format(float(v) * 100, ".32f"), 2)


def truncate(f, n):
    """Truncates/pads a float f to n decimal places without rounding"""
    s = "{}".format(f)
    if "e" in s or "E" in s:
        return "{0:.{1}f}".format(f, n)
    i, p, d = s.partition(".")
    return ".".join([i, (d + "0" * n)[:n]])


def str_number(v):
    """接收一个整数，返回 xxk 的方式"""
    v = int(v)
    if v > 10000000:
        return "%.2f千万" % (v / float(10000000))
    if v > 10000:
        return "%.2f万" % (v / float(10000))
    return str(v)


def str_msecs(v):
    """接收毫秒数"""
    v = int(v)
    if v > 1000:
        return "%.2fs" % (v / float(1000))
    return "%sms" % v


RE_TIME_STR = re.compile(r"^(\d+)(\w)$")


def str_to_seconds(s):
    """将形如 24h 的字符串转换为秒数

    :param str s: 表示时间的字符串，形如 24h
    """
    time_unit_to_seconds = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 3600 * 24,
    }
    s = s.lower()
    try:
        value, unit = RE_TIME_STR.match(s.lower()).groups()
        return int(value) * time_unit_to_seconds[unit]
    except Exception:
        raise ValueError("Invalid time string given")
