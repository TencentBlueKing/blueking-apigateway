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

from rest_framework import status
from rest_framework.renderers import JSONRenderer


class BkStandardApiJSONRenderer(JSONRenderer):
    """Renderer which wraps original JSON response with an extra layer.

    Normal
    - Original: `{"foo": [1, 2]}`
    - Wrapped: `{"data": {"foo": [1, 2]}}`

    Error
    - Original: `{"code": "xxxx",...}`
    - Wrapped: `{"error": {"code": "xxxx",...}}`
    """

    format = "bk_std_json"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Wrap response data on demand
        resp = renderer_context["response"]
        # NOTE: 204 no content should not wrap with a content, the request would be pending forever
        if status.is_success(resp.status_code) and resp.status_code != 204:
            data = {"data": data}
        elif (
            status.is_client_error(resp.status_code) or status.is_server_error(resp.status_code)
        ) and "error" not in data:
            # the error from exception_handler already wrap the error data, so we don't need to wrap it again
            data = {"error": data}
        # For status codes other than (2xx, 4xx, 5xx), do not wrap data
        return super().render(data, accepted_media_type=None, renderer_context=None)
