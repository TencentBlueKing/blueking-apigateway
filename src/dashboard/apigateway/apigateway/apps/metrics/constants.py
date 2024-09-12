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


class MetricsEnum(StructuredEnum):
    REQUESTS = EnumField("requests")
    FAILED_REQUESTS = EnumField("failed_requests")
    RESPONSE_TIME_95TH = EnumField("response_time_95th")
    RESPONSE_TIME_90TH = EnumField("response_time_90th")
    RESPONSE_TIME_80TH = EnumField("response_time_80th")
    RESPONSE_TIME_50TH = EnumField("response_time_50th")


class DimensionEnum(StructuredEnum):
    ALL = EnumField("all")
    APP = EnumField("app")
    RESOURCE = EnumField("resource")
    # 资源+非200状态码
    RESOURCE_NON200_STATUS = EnumField("resource_non200_status")
