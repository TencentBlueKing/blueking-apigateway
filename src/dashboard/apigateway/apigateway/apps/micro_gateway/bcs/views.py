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
import logging
import operator

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.micro_gateway.bcs import serializers
from apigateway.common.error_codes import error_codes
from apigateway.components.bcs_helper import BcsApiGatewayApiRequestError, BcsHelper
from apigateway.controller.helm.release import ReleaseHelper
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.responses import OKJsonResponse

logger = logging.getLogger(__name__)


class BcsViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.BcsProjectSLZ(many=True)}, tags=["MicroGateway.BCS"]
    )
    def get_projects(self, request, *args, **kwargs):
        try:
            projects = BcsHelper(access_token=get_user_access_token_from_request(request)).get_projects()
        except BcsApiGatewayApiRequestError as err:
            raise error_codes.REMOTE_REQUEST_ERROR.format(str(err), replace=True)

        slz = serializers.BcsProjectSLZ(projects, many=True)
        return OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("project_name")))

    @swagger_auto_schema(
        query_serializer=serializers.QueryBcsClusterSLZ,
        responses={status.HTTP_200_OK: serializers.BcsClusterSLZ(many=True)},
        tags=["MicroGateway.BCS"],
    )
    def get_clusters(self, request, *args, **kwargs):
        query_slz = serializers.QueryBcsClusterSLZ(data=request.query_params)
        query_slz.is_valid(raise_exception=True)

        try:
            clusters = BcsHelper(access_token=get_user_access_token_from_request(request)).get_clusters(
                project_id=query_slz.validated_data["project_id"]
            )
        except BcsApiGatewayApiRequestError as err:
            raise error_codes.REMOTE_REQUEST_ERROR.format(str(err), replace=True)

        slz = serializers.BcsClusterSLZ(clusters, many=True)
        return OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("cluster_id")))

    @swagger_auto_schema(
        query_serializer=serializers.QueryBcsNamespaceSLZ,
        responses={status.HTTP_200_OK: serializers.BcsNamespaceSLZ(many=True)},
        tags=["MicroGateway.BCS"],
    )
    def get_namespaces(self, request, *args, **kwargs):
        query_slz = serializers.QueryBcsNamespaceSLZ(data=request.query_params)
        query_slz.is_valid(raise_exception=True)

        data = query_slz.validated_data

        try:
            namespaces = BcsHelper(access_token=get_user_access_token_from_request(request)).get_namespaces(
                project_id=data["project_id"],
                cluster_id=data["cluster_id"],
            )
        except BcsApiGatewayApiRequestError as err:
            raise error_codes.REMOTE_REQUEST_ERROR.format(str(err), replace=True)

        slz = serializers.BcsNamespaceSLZ(namespaces, many=True)
        return OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("namespace")))

    @swagger_auto_schema(
        query_serializer=serializers.QueryBcsReleaseSLZ,
        responses={status.HTTP_200_OK: serializers.BcsReleaseSLZ(many=True)},
        tags=["MicroGateway.BCS"],
    )
    def get_releases(self, request, *args, **kwargs):
        query_slz = serializers.QueryBcsReleaseSLZ(data=request.query_params)
        query_slz.is_valid(raise_exception=True)

        data = query_slz.validated_data

        try:
            releases = ReleaseHelper(access_token=get_user_access_token_from_request(request)).list_releases(
                project_id=data["project_id"],
                cluster_id=data["cluster_id"],
                namespace=data["namespace"],
            )
        except BcsApiGatewayApiRequestError as err:
            raise error_codes.REMOTE_REQUEST_ERROR.format(str(err), replace=True)

        # 根据 chart 名称，过滤出微网关实例
        matched_releases = filter(lambda x: x.chart_name == settings.BCS_MICRO_GATEWAY_CHART_NAME, releases)

        slz = serializers.BcsReleaseSLZ(matched_releases, many=True)
        return OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("release_name")))
