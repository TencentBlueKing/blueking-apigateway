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
import enum

from attrs import define, field

from apigateway.utils.measurement import MeasurementPoint


class MicroGatewayStatus(enum.IntFlag):
    OK = 0
    # 未知异常
    UNKNOWN_ERROR = 1
    # 基础信息异常
    BASIC_INFO_ERROR = 1 << 1
    # 网关状态异常
    GATEWAY_ERROR = 1 << 2
    # 控制平面异常
    CONTROL_PLANE_ERROR = 1 << 3
    # 数据平面异常
    DATA_PLANE_ERROR = 1 << 4

    @classmethod
    def convert(cls, value):
        if isinstance(value, cls):
            return value

        return cls(int(value))


@define
class MicroGatewayStatusMeasurementPoint(MeasurementPoint):
    """网关状态测量点"""

    measurement = "gateway-status"
    # 网关汇总状态，当这个值不为 0 时，表示网关异常，请根据状态位以及细化的状态来判断具体的异常
    status: MicroGatewayStatus = field(converter=MicroGatewayStatus.convert)  # type: ignore
    # 副本数量
    replicas: int = field(converter=int)
    # 控制面异常数量
    control_plane_failures: int = field(converter=int)
    # 控制面状态码
    control_plane_status: int = field(converter=int)
    # 数据面异常数量
    data_plane_failures: int = field(converter=int)
    # 数据面状态码
    data_plane_status: int = field(converter=int)
    # 正常副本数量
    success_replicas: int = field(converter=int)
