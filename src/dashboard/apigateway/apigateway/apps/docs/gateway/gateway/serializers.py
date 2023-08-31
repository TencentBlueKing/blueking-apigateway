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
from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.core.constants import GatewayTypeEnum


class GatewayQuerySLZ(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)
    user_auth_type = serializers.CharField(required=False, allow_blank=True)


class GatewaySLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    maintainers = serializers.ListField()
    user_auth_type = serializers.CharField()
    user_auth_type_display = serializers.SerializerMethodField()
    name_prefix = serializers.SerializerMethodField()
    api_url = serializers.SerializerMethodField()

    def get_name_prefix(self, obj):
        if obj["api_type"] in [GatewayTypeEnum.SUPER_OFFICIAL_API.value, GatewayTypeEnum.OFFICIAL_API.value]:
            return _("[官方]")
        return ""

    def get_user_auth_type_display(self, obj):
        return UserAuthTypeEnum.get_choice_label(obj["user_auth_type"])

    def get_api_url(self, obj):
        return getattr(settings, "BK_API_URL_TMPL", "").format(api_name=obj["name"])
