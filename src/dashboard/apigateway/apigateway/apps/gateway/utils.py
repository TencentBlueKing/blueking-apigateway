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
from typing import Dict

from django.conf import settings

from apigateway.core.constants import APIHostingTypeEnum, DefaultGatewayFeatureFlag, MicroGatewayFeatureFlag


def get_gateway_feature_flags(hosting_type: APIHostingTypeEnum) -> Dict[str, bool]:
    """获取网关功能特性开关"""
    if hosting_type == APIHostingTypeEnum.DEFAULT:
        gateway_feature_flags = DefaultGatewayFeatureFlag
    elif hosting_type == APIHostingTypeEnum.MICRO:
        gateway_feature_flags = MicroGatewayFeatureFlag
    else:
        raise ValueError(f"unsupported hosting_type={hosting_type.value}")

    feature_flags = gateway_feature_flags.get_default_flags()

    # 合并全局的网关特性开关
    for key, flag in settings.GLOBAL_GATEWAY_FEATURE_FLAG.items():
        feature_flags.setdefault(key, flag)

        # 若全局开关未开启，则网关特性开关也不开启
        if flag is False:
            feature_flags[key] = False

    return feature_flags
