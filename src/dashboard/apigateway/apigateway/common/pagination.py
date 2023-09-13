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

from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from apigateway.utils.conv import str_bool


class StandardLimitOffsetPagination(LimitOffsetPagination):
    """
    对 DRF LimitOffsetPagination 进行扩展，获取分页数据
    """

    # 不分页时，limit 指定一个较大值，以便返回全量数据
    _no_page_limit = 1000000000

    def _is_legacy_api(self, request) -> bool:
        return request and "/backend/api/v1/" in request.path

    def get_paginated_response(self, data):
        # for legacy api
        if self._is_legacy_api(self.request):
            return super().get_paginated_response(data)

        return Response(OrderedDict([("data", OrderedDict([("count", self.count), ("results", data)]))]))

    def get_limit(self, request):
        limit = super().get_limit(request)
        # for legacy api
        if self._is_legacy_api(request):
            # support no_page
            no_page = str_bool(request.query_params.get("no_page", False), allow_null=True)
            if no_page and limit is not None:
                return self._no_page_limit
            return limit

        # NOTE: new api should not support `no_page`!!!!!!
        return limit

    def get_paginated_data(self, data: list) -> dict:
        # for legacy api
        if self._is_legacy_api(self.request):
            return {
                "count": self.count,
                "has_next": bool(self.get_next_link()),
                "has_previous": bool(self.get_previous_link()),
                "results": data,
            }

        # NOTE: new api should not call this func, use return `self.get_paginated_response(serializer.data)`
        raise NotImplementedError
