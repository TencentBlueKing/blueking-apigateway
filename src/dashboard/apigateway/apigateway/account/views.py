# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from rest_framework.views import APIView

from apigateway.utils.responses import OKJsonResponse


class UserAPIView(APIView):
    """
    用户信息 相关
    get: 当前登录用户信息
    """

    def get(self, request, *args, **kwargs):
        user = request.user
        data = {
            "chinese_name": getattr(user, "chinese_name", ""),
            "avatar_url": getattr(user, "avatar_url", ""),
            "username": user.username,
            "display_name": getattr(user, "display_name", "") or user.username,
            "tenant_id": getattr(user, "tenant_id", ""),
        }
        return OKJsonResponse(data=data)
