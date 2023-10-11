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
import copy

from django.conf import settings
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.feature.models import UserFeatureFlag
from apigateway.utils.responses import OKJsonResponse


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取全局特性开关",
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Feature"],
    ),
)
class FeatureFlagListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        """获取特性开关列表"""
        feature_flags = copy.copy(settings.DEFAULT_FEATURE_FLAG)
        feature_flags.update(
            {
                "MENU_ITEM_ESB_API": feature_flags.get("MENU_ITEM_ESB_API", False) and request.user.is_superuser,
                "MENU_ITEM_ESB_API_DOC": feature_flags.get("MENU_ITEM_ESB_API_DOC", False),
            }
        )

        user_feature_flags = UserFeatureFlag.objects.get_feature_flags(request.user.username)
        feature_flags.update(user_feature_flags)

        return OKJsonResponse(data=feature_flags)
