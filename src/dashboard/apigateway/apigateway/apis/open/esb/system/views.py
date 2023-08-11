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
from typing import List

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.esb.system import serializers
from apigateway.apps.esb.bkcore.models import ComponentSystem, ESBChannel
from apigateway.utils.responses import V1OKJsonResponse


class SystemViewSet(viewsets.GenericViewSet):
    api_permission_exempt = True

    def _filter_active_and_public_systems(self, boards: List[str]):
        """
        获取可用的组件系统列表
        """
        system_ids = ESBChannel.objects.filter_active_and_public_system_ids(
            boards=boards,
            allow_apply_permission=True,
        )

        return ComponentSystem.objects.filter(board__in=boards, id__in=system_ids)

    @swagger_auto_schema(
        query_serializer=serializers.SystemQueryV1SLZ,
        responses={status.HTTP_200_OK: serializers.SystemV1SLZ(many=True)},
        tags=["OpenAPI.ESB.System"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.SystemQueryV1SLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = self._filter_active_and_public_systems(boards=slz.validated_data["boards"])

        slz = serializers.SystemV1SLZ(queryset.order_by("board", "name"), many=True)
        return V1OKJsonResponse("OK", data=slz.data)
