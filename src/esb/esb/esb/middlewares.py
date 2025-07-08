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

import time
from builtins import object

from django.conf import settings

from common.base_utils import FancyDict, str_bool
from common.django_utils import JsonResponse
from common.errors import APIError
from esb.response import format_resp_dict

"""
Middlewares for ESB
"""


class DebugHelperMiddleware(object):
    """
    Helper for debug
    """

    def process_request(self, request):
        if not settings.DEBUG:
            return

        # 判断是否跳过signature验证
        request.__esb_skip_signature__ = False
        # 判断是否跳过组件权限验证
        request.__esb_skip_comp_perm__ = False
        if str_bool(request.GET.get("__esb_skip_signature__")):
            request.__esb_skip_signature__ = True

        if str_bool(request.GET.get("__esb_skip_comp_perm__")):
            request.__esb_skip_comp_perm__ = True


class APICommonMiddleware(object):
    """
    Common middleware for ESB API
    """

    def process_request(self, request):
        # 设置一些默认值
        request.g = FancyDict(path_vars=None, comp_path=None, ts_request_start=time.time())

    def process_exception(self, request, exception):
        """
        Capture APIError and replace it with user-friendly error response
        """
        if isinstance(exception, APIError):
            response = format_resp_dict(exception.code.as_dict())
            return JsonResponse(response, status=exception.code.status)
