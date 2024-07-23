from typing import Dict, Literal, Optional

from django.conf import settings
from pydantic import BaseModel, Field, root_validator, validator


class Authorization(BaseModel):
    bk_app_code: Optional[str] = Field(None, help="蓝鲸应用编码")
    bk_app_secret: Optional[str] = Field(None, help="蓝鲸应用密钥")
    bk_ticket: Optional[str] = Field(None, help="蓝鲸用户票据")
    bk_token: Optional[str] = Field(None, help="蓝鲸用户票据")  # 注意：这里可能是一个重复字段，根据实际需求调整
    uin: Optional[str] = Field(None, help="uin")
    skey: Optional[str] = Field(None, help="skey")

    @validator("uin", allow_reuse=True)
    def validate_uin(cls, v):
        if v is not None:
            return v.lstrip("o0")
        return v

    @root_validator(pre=True, allow_reuse=True)
    def remove_empty_values(cls, values):
        return {k: v for k, v in values.items() if v is not None and v.strip()}


class APITestRequestBuilder(BaseModel):
    stage_id: int
    resource_id: int
    method: Literal["GET", "POST", "PUT", "DELETE"] = Field("GET", help="HTTP 方法，默认为GET")
    subpath: Optional[str] = Field(None, help="子路径")
    headers: Dict[str, str] = Field({}, help="请求头")
    path_params: Dict[str, str] = Field({}, help="路径参数")
    query_params: Dict[str, str] = Field({}, help="查询参数")
    body: Optional[str] = Field(None, help="请求体")
    use_test_app: bool = Field(False, help="是否使用测试应用")
    use_user_from_cookies: bool = Field(False, help="是否使用 cookies 中的用户信息")
    authorization: Optional[Authorization] = Field(None, help="认证信息")

    @validator("authorization", pre=True, always=True)
    def validate_authorization(cls, v, values):
        if values.get("use_test_app"):
            return Authorization(**settings.DEFAULT_TEST_APP)
        return v
