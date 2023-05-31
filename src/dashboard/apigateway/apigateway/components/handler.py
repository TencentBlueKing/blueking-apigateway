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
from typing import Any, Callable, Dict, Optional, Tuple

from attrs import define
from bkapi_client_core.exceptions import BKAPIError
from requests import Response

from apigateway.components.exceptions import RemoteAPIResultError, RemoteRequestError


@define(slots=False)
class RequestAPIHandler:
    name: str
    parse_response: Callable

    def call_api(self, operation, *args, **kwargs) -> Tuple[Dict[str, Any], Response]:
        try:
            response = getattr(operation, "request")(*args, **kwargs)
        except BKAPIError as err:
            raise RemoteRequestError(self.name, err)

        try:
            return self.parse_response(operation, response), response
        except BKAPIError as err:
            raise RemoteRequestError(self.name, err)

    def parse_api_result(
        self,
        api_result: Dict[str, Any],
        response: Response,
        validate_conditions: Optional[Dict] = None,
        convertor: Optional[Callable] = None,
    ):
        if validate_conditions:
            for key, expected_value in validate_conditions.items():
                if api_result.get(key) == expected_value:
                    continue

                raise RemoteAPIResultError(self.name, response, api_result.get("message", "unknown error"))

        if convertor:
            return convertor(api_result)

        return api_result
