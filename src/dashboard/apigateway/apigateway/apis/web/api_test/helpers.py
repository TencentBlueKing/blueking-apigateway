from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


class ApiDebugHistoryRequest(BaseModel):
    request_url: Optional[str] = Field(help="请求路由")
    request_method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] = Field(
        "GET", help="HTTP 方法，默认为GET"
    )
    type: Literal["HTTP", "GRPC", "WEBSOCKET"] = Field("HTTP", help="请求类型，默认为HTTP")
    authorization: Dict[str, str] = Field(None, help="认证信息")
    path_params: Dict[str, str] = Field({}, help="路径参数")
    query_params: Dict[str, str] = Field({}, help="查询参数")
    body: Optional[str] = Field(None, help="请求体")
    headers: Dict[str, str] = Field({}, help="请求头")
    subpath: Optional[str] = Field(None, help="子路径")
    use_test_app: bool = Field(False, help="是否使用测试应用")
    use_user_from_cookies: bool = Field(False, help="是否使用 cookies 中的用户信息")
    request_time: Optional[datetime] = Field(None, help="请求时间")
    spec_version: Optional[int] = Field(1, help="请求版本")


class ApiDebugHistoryResponse(BaseModel):
    status_code: Optional[int] = Field(200, help="返回结果的状态码")
    proxy_time: float = Field(..., gt=0, help="处理时间，单位为秒，包含两位小数")
    body: Optional[str] = Field(None)
    spec_version: Optional[int] = Field(1, help="返回的结果版本")

    # 格式化时间
    def format_proxy_time(self) -> str:
        return f"{self.proxy_time:.2f}"
