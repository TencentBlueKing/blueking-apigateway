# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
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


class BoundedLimitOffsetPagination(StandardLimitOffsetPagination):
    """Limit/offset pagination that rejects non-integer or out-of-range query params."""

    default_limit = 10
    max_limit = 20

    def get_limit(self, request):
        raw_limit = request.query_params.get(self.limit_query_param)
        if raw_limit is not None:
            try:
                limit = int(raw_limit)
            except TypeError, ValueError:
                raise ValidationError({"limit": [_("limit 必须为整数。")]})
            if not 1 <= limit <= self.max_limit:
                raise ValidationError(
                    {"limit": [_("limit 必须在 1 到 %(max_limit)s 之间。") % {"max_limit": self.max_limit}]}
                )
        return super().get_limit(request)

    def get_offset(self, request):
        raw_offset = request.query_params.get(self.offset_query_param)
        if raw_offset is not None:
            try:
                offset = int(raw_offset)
            except TypeError, ValueError:
                raise ValidationError({"offset": [_("offset 必须为整数。")]})
            if offset < 0:
                raise ValidationError({"offset": [_("offset 必须大于或等于 0。")]})
        return super().get_offset(request)
