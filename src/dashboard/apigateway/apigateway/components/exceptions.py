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
from bkapi_client_core.exceptions import BKAPIError, ResponseError
from requests import Response


class RemoteRequestError(Exception):
    def __init__(self, name: str, error: BKAPIError):
        self.name = name
        self.error = error

    def __str__(self):
        parts = []

        parts.append(f"request {self.name} error!")

        request_info = self._get_request_info()
        if request_info:
            parts.append(request_info)

        parts.append(f"Error=[{self.error}]")

        return " ".join(parts)

    def _get_request_info(self) -> str:
        if not (isinstance(self.error, ResponseError) and self.error.request):
            return ""

        return f"Request=[{self.error.request.method} {self.error.request.url}]"


class RemoteAPIResultError(Exception):
    def __init__(self, name: str, response: Response, message: str):
        self.name = name
        self.response = response
        self.message = message

    def __str__(self):
        parts = []

        parts.append(f"request {self.name} fail!")

        request = self.response.request
        request_id = self.response.headers.get("X-Bkapi-Request-Id", "")
        parts.append(f"Request=[{request.method} {request.url}, request_id={request_id}]")

        parts.append(f"Response=[status_code={self.response.status_code}, {self.message}]")

        return " ".join(parts)


class ApiRequestError(Exception):
    """API 请求错误"""
