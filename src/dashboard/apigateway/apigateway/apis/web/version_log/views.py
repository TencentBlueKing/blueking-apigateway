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

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.utils.responses import OKJsonResponse

from .serializers import VersionLogSLZ
from .utils import get_version_list


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="版本信息",
        responses={status.HTTP_200_OK: VersionLogSLZ(label="版本信息", many=True)},
        tags=["version_log"],
    ),
)
class VersionLogListApi(generics.ListAPIView):
    authentication_classes = []  # type: ignore
    permission_classes = []  # type: ignore
    pagination_class = None  # 去掉 swagger 中的 limit offset 参数

    def get(self, request, *args, **kwargs):
        data = get_version_list()
        return OKJsonResponse(data=data)
