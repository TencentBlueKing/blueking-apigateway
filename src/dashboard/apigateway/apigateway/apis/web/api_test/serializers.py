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
from typing import Any, Dict

from django.conf import settings
from rest_framework import serializers

from apigateway.core.constants import HTTP_METHOD_CHOICES


class AuthorizationSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(allow_blank=True, required=False)
    bk_app_secret = serializers.CharField(allow_blank=True, required=False)
    bk_ticket = serializers.CharField(allow_blank=True, required=False)
    bk_token = serializers.CharField(allow_blank=True, required=False)
    uin = serializers.CharField(allow_blank=True, required=False)
    skey = serializers.CharField(allow_blank=True, required=False)

    def validate_uin(self, value):
        try:
            return value.lstrip("o0")
        except Exception:
            return value

    def validate(self, data: Dict[str, str]) -> Dict[str, str]:
        return {k: v for k, v in data.items() if v}


class APITestInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField()
    resource_id = serializers.IntegerField()
    method = serializers.ChoiceField(choices=HTTP_METHOD_CHOICES)
    subpath = serializers.CharField(allow_blank=True, required=False)
    headers = serializers.DictField(child=serializers.CharField(), allow_empty=True)
    path_params = serializers.DictField(child=serializers.CharField(), allow_empty=True)
    query_params = serializers.DictField(child=serializers.CharField(), allow_empty=True)
    body = serializers.CharField(allow_blank=True, required=False)
    use_test_app = serializers.BooleanField()
    use_user_from_cookies = serializers.BooleanField(required=False, default=False)
    authorization = AuthorizationSLZ(required=False, allow_null=True)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data.setdefault("authorization", {})
        if data.get("use_test_app"):
            data["authorization"].update(settings.DEFAULT_TEST_APP)

        return data


class APITestOutputSLZ(serializers.Serializer):
    status_code = serializers.IntegerField()
    proxy_time = serializers.IntegerField()
    size = serializers.FloatField()
    body = serializers.CharField()
    headers = serializers.DictField()
