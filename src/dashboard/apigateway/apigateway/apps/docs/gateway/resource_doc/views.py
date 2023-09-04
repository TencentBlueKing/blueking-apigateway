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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.docs.gateway.resource_doc.helpers import ResourceDocHelper
from apigateway.apps.docs.helper import support_helper
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import V1OKJsonResponse

from .serializers import ResourceDocSLZ


class ResourceDocViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["APIGateway.ResourceDoc"],
    )
    def retrieve(self, request, gateway_name: str, stage_name: str, resource_name: str, *args, **kwargs):
        """获取网关资源的文档"""
        gateway = support_helper.get_gateway_by_name(gateway_name)
        if not gateway:
            raise error_codes.NOT_FOUND

        data = support_helper.get_resource_doc(gateway["id"], stage_name, resource_name)
        helper = ResourceDocHelper(
            stage_name,
            data["resource"] or {},
            data["doc"] or {},
            data["resource_url"] or "",
            gateway["maintainers"],
        )

        doc = helper.get_doc()
        if not doc:
            raise error_codes.NOT_FOUND

        slz = ResourceDocSLZ(doc)
        return V1OKJsonResponse("OK", data=slz.data)
