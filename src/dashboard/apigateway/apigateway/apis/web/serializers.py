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
from rest_framework import serializers

from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN

from .constants import BackendConfigSchemeEnum, BackendConfigTypeEnum, LoadBalanceTypeEnum


class HostSLZ(serializers.Serializer):
    scheme = serializers.ChoiceField(choices=BackendConfigSchemeEnum.get_choices())
    host = serializers.RegexField(HOST_WITHOUT_SCHEME_PATTERN)
    weight = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        ref_name = "apis.web.HostSLZ"


class BaseBackendConfigSLZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=BackendConfigTypeEnum.get_choices(), default=BackendConfigTypeEnum.NODE.value
    )
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices())
    hosts = serializers.ListField(child=HostSLZ(), allow_empty=False)
