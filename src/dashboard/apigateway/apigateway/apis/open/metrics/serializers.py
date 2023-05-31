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

from apigateway.common.fields import TimestampField


class StatisticsAPIRequestQueryV1SLZ(serializers.Serializer):
    start_time = TimestampField(allow_null=False, required=True)
    end_time = TimestampField(allow_null=False, required=True)


class StatisticsAPIRequestV1SLZ(serializers.Serializer):
    api_id = serializers.IntegerField(read_only=True)
    api_name = serializers.SerializerMethodField()
    api_maintainers = serializers.SerializerMethodField()
    total_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    bk_app_code_list = serializers.SerializerMethodField()

    def get_api_name(self, obj):
        api = self.context["api_id_map"].get(obj["api_id"])
        return api.name if api else ""

    def get_api_maintainers(self, obj):
        api = self.context["api_id_map"].get(obj["api_id"])
        return api.maintainers if api else ""

    def get_bk_app_code_list(self, obj):
        return self.context["app_request_data"].get(obj["api_id"], {}).get("bk_app_code_list", [])
