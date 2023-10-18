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
# 1.13 版本：兼容旧版 (api_version=0.1) 资源 yaml 通过 openapi 导入
import re

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.core.constants import DEFAULT_LB_HOST_WEIGHT, STAGE_VAR_REFERENCE_PATTERN, LoadBalanceTypeEnum

# 通过 openapi 导入时，只允许导入使用环境变量的后端地址
RESOURCE_DOMAIN_PATTERN = re.compile(r"^http(s)?:\/\/\{%s\}$" % (STAGE_VAR_REFERENCE_PATTERN.pattern))

HEADER_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9-]{1,100}$")


class LegacyResourceHostSLZ(serializers.Serializer):
    host = serializers.RegexField(RESOURCE_DOMAIN_PATTERN)
    weight = serializers.IntegerField(min_value=1, default=DEFAULT_LB_HOST_WEIGHT)


class LegacyUpstreamsSLZ(serializers.Serializer):
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices(), required=False)
    hosts = serializers.ListField(child=LegacyResourceHostSLZ(), allow_empty=False, required=False)

    def validate(self, data):
        if "hosts" in data and not data.get("loadbalance"):
            raise serializers.ValidationError(_("hosts 存在时，需要指定 loadbalance 类型。"))

        return data


class LegacyTransformHeadersSLZ(serializers.Serializer):
    set = serializers.DictField(label="设置", child=serializers.CharField(), required=False, allow_empty=True)
    delete = serializers.ListField(label="删除", child=serializers.CharField(), required=False, allow_empty=True)

    def _validate_headers_key(self, value):
        for key in value:
            if not HEADER_KEY_PATTERN.match(key):
                raise serializers.ValidationError(_("Header 键由字母、数字、连接符（-）组成，长度小于100个字符。"))
        return value

    def validate_set(self, value):
        return self._validate_headers_key(value)

    def validate_delete(self, value):
        return self._validate_headers_key(value)
