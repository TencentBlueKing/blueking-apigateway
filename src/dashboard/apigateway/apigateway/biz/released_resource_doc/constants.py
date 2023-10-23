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
from blue_krill.data_types.enum import EnumField, StructuredEnum

from apigateway.apps.support.constants import DocLanguageEnum


class APIDocTypeEnum(StructuredEnum):
    MARKDOWN = EnumField("markdown")


BKAPI_AUTHORIZATION_DESCRIPTION_ZH = """
{%- if verified_app_required or verified_user_required %}
### 公共请求参数

公共请求参数是用于标识应用和用户的参数，如果云 API 接口需要认证应用或用户，则请求时需要携带这些参数，才能正常发起请求。公共请求参数，可通过请求头 `X-Bkapi-Authorization` 传递，值为 JSON 格式字符串。{%- if docs_urls.USE_GATEWAY_API %}详情请查看 [调用网关 API]({{ docs_urls.USE_GATEWAY_API }}){%- endif %}

**示例：** 使用 curl 命令，请求时携带认证请求头

```shell
{%- if verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "demo", "bk_app_secret": "secret", "bk_token": "your_token"}' "http://example.com/api"
{%- else %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "demo", "bk_app_secret": "secret"}' "http://example.com/api"
{%- endif %}
```

**示例：** 使用 Python 语言和 requests 模块

```python
import json
import requests

requests.get(
    "http://example.com/api",
    headers={
        "X-Bkapi-Authorization": json.dumps({
            "bk_app_code": "demo",
            "bk_app_secret": "secret",
            {%- if verified_user_required %}
            "bk_token": "your_token",
            {%- endif %}
        })
    },
)
```

`X-Bkapi-Authorization` 请求头所支持的全部字段如下表所示：

| 字段  | 类型 | 必选 |  描述 |
|-----------|------------|--------|------------|
{%- if verified_app_required %}
| bk_app_code   | string  |  否 | 应用 ID，可以通过`蓝鲸开发者中心 -> 应用基本设置 -> 基本信息 -> 鉴权信息`获取；*网关 SDK 默认已添加* |
| bk_app_secret | string  |  否 | 安全秘钥，可以通过`蓝鲸开发者中心 -> 应用基本设置 -> 基本信息 -> 鉴权信息`获取；*网关 SDK 默认已添加* |
{%- endif %}
| access_token  | string  |  否 | 用户或应用 access_token{%- if docs_urls.ACCESS_TOKEN_API %}，详情参考 [AccessToken API]({{ docs_urls.ACCESS_TOKEN_API }}){%- endif %} |
{%- if verified_user_required %}
| bk_token      | string  |  否 | 用户登录态，用于认证用户；登录蓝鲸，对应 Cookies 中 bk_token 字段的值；提供 bk_token 时，不需要再提供 bk_username |
| bk_username   | string  |  否 | 当前用户用户名；仅用于应用免用户认证的场景中，用于指定当前用户。应用需向网关管理员申请免用户认证白名单，由于用户未经过校验，存在安全风险，请谨慎使用 |
{%- endif %}
{%- endif %}
"""  # noqa


BKAPI_AUTHORIZATION_DESCRIPTION_EN = """
{%- if verified_app_required or verified_user_required %}
### Public Request Parameters

Public request parameters are parameters used to identify the application and user. If the cloud API requires authentication of the application or user, the request needs to carry these parameters in order to initiate the request properly. The public request parameters, which can be passed through the request header `X-Bkapi-Authorization`, have the value as a JSON formatted string.

**Example：** Use `curl` to carry the authorization header

```shell
{%- if verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "demo", "bk_app_secret": "secret", "bk_token": "your_token"}' "http://example.com/api"
{%- else %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "demo", "bk_app_secret": "secret"}' "http://example.com/api"
{%- endif %}
```

**Example：** Use Python and the `requests` module

```python
import json
import requests

requests.get(
    "http://example.com/api",
    headers={
        "X-Bkapi-Authorization": json.dumps({
            "bk_app_code": "demo",
            "bk_app_secret": "secret",
            {%- if verified_user_required %}
            "bk_token": "your_token",
            {%- endif %}
        })
    },
)
```

The supported fields of the header `X-Bkapi-Authorization` are shown in the following table:

| Field  | Type | Required |  Description |
|-----------|------------|--------|------------|
{%- if verified_app_required %}
| bk_app_code   | string  |  No | App ID, can get from `Developer Center -> App Settings -> Basic Information -> Authentication Information`; *Gateway SDK added by default* |
| bk_app_secret | string  |  No | App Secret, can get from `Developer Center -> App Settings -> Basic Information -> Authentication Information`; *Gateway SDK added by default* |
{%- endif %}
| access_token  | string  |  No | User or App access_token{%- if docs_urls.ACCESS_TOKEN_API %}, details [AccessToken API]({{ docs_urls.ACCESS_TOKEN_API }}){%- endif %} |
{%- if verified_user_required %}
| bk_token      | string  |  No | User login token, used to authenticate user; login to BlueKing, corresponding to the value of the bk_token field in Cookies; when providing bk_token, there is no need to provide bk_username |
| bk_username   | string  |  No | Current user username, user verification exempted apps, use this field to specify the current user; app need to apply to gateway managers for user authentication-free whitelist, since user has not been verified, there are security risks, so please use it with caution |
{%- endif %}
{%- endif %}
"""  # noqa


BKAPI_AUTHORIZATION_DESCRIPTIONS = {
    DocLanguageEnum.ZH.value: BKAPI_AUTHORIZATION_DESCRIPTION_ZH,
    DocLanguageEnum.EN.value: BKAPI_AUTHORIZATION_DESCRIPTION_EN,
}

RESOURCE_URL_PART_ZH = """
### API地址
| 环境   | 请求方法  | 请求地址  |
| ------ | --------- | ---------- |
| {stage_name} | {method} | {resource_url} |
"""


RESOURCE_URL_PART_EN = """
### API Path
| Stage   | Request method  | Request url  |
| ------ | --------- | ---------- |
| {stage_name} | {method} | {resource_url} |
"""

RESOURCE_URL_PARTS = {
    DocLanguageEnum.ZH.value: RESOURCE_URL_PART_ZH,
    DocLanguageEnum.EN.value: RESOURCE_URL_PART_EN,
}
