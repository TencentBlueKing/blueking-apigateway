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
from rest_framework import generics

from apigateway.utils.responses import OKJsonResponse

from .constants import USER_AUTH_TYPES
from .serializers import UserAuthTypeInputSLZ


class UserTokenGetApi(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        # TODO: 此接口待删除
        return OKJsonResponse(
            data=self._get_ticket_from(settings.BK_LOGIN_TICKET_KEY_TO_COOKIE_NAME),
        )

    def _get_ticket_from(self, key_to_cookie_name_map: dict) -> dict:
        return {key: "" for key, _ in key_to_cookie_name_map.items()}


class UserAuthTypeListApi(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        slz = UserAuthTypeInputSLZ(USER_AUTH_TYPES, many=True)
        return OKJsonResponse(
            data=slz.data,
        )
