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
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


class ApiDebugHistoryRequest(BaseModel):
    request_url: Optional[str] = Field(help="请求路由")
    request_method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] = Field(
        "GET", help="HTTP 方法，默认为GET"
    )
    type: Literal["HTTP", "GRPC", "WEBSOCKET"] = Field("HTTP", help="请求类型，默认为HTTP")
    path_params: Dict[str, str] = Field({}, help="路径参数")
    query_params: Dict[str, str] = Field({}, help="查询参数")
    body: Optional[str] = Field(None, help="请求体")
    headers: Dict[str, str] = Field({}, help="请求头")
    subpath: Optional[str] = Field(None, help="子路径")
    use_test_app: bool = Field(False, help="是否使用测试应用")
    use_user_from_cookies: bool = Field(False, help="是否使用 cookies 中的用户信息")
    spec_version: Optional[int] = Field(1, help="请求版本")


class ApiDebugHistoryResponse(BaseModel):
    body: Optional[dict] = Field(None, help="调用成功的时候跟返回结果一致")
    spec_version: Optional[int] = Field(1, help="返回的结果版本")
    error: Optional[str] = Field(None, help="错误信息")

    # 格式化时间
    def format_proxy_time(self) -> str:
        return f"{self.proxy_time:.2f}"
