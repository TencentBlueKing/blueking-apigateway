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
from django.utils.deprecation import MiddlewareMixin

from apigateway.utils.local import local
from apigateway.utils.string import generate_unique_id


class RequestIDMiddleware(MiddlewareMixin):
    """
    request_id 中间件
    """

    def __call__(self, request):
        local.request = request
        request.request_id = generate_unique_id()

        response = self.get_response(request)
        response["X-Request-Id"] = request.request_id

        local.release()

        return response
