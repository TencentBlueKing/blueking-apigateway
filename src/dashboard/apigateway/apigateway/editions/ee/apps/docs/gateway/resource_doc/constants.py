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
from apigateway.common.constants import ChoiceEnum, LanguageCodeEnum


class APIDocTypeEnum(ChoiceEnum):
    MARKDOWN = "markdown"


BKAPI_AUTHORIZATION_DESCRIPTION_ZH = """
{%- if app_verified_required or user_verified_required %}
### 公共请求参数

公共请求参数是用于标识应用和用户的参数，如果云 API 接口需要认证应用或用户，则请求时需要携带这些参数，才能正常发起请求。公共请求参数，可通过请求头 `X-Bkapi-Authorization` 传递，值为 JSON 格式字符串。

**示例：** 使用 curl 命令，请求时携带认证请求头

```shell
curl -H 'X-Bkapi-Authorization: {"access_token": "your_token"}' "http://example.com/api"
```

**示例：** 使用 Python 语言和 requests 模块

```python
import json
import requests

requests.get(
    'http://example.com/api',
    headers={
        'X-Bkapi-Authorization': json.dumps({'access_token': 'your_token'})
    },
)
```

`X-Bkapi-Authorization` 请求头所支持的全部字段如下表所示：

| 字段  | 类型 | 必选 |  描述 |
|-----------|------------|--------|------------|
{%- if app_verified_required %}
| bk_app_code   | string  |  否 | 应用 ID，可以通过`蓝鲸开发者中心 -> 应用基本设置 -> 基本信息 -> 鉴权信息`获取；*网关 SDK 默认已添加* |
| bk_app_secret | string  |  否 | 安全秘钥，可以通过`蓝鲸开发者中心 -> 应用基本设置 -> 基本信息 -> 鉴权信息`获取；*网关 SDK 默认已添加* |
{%- endif %}
| access_token  | string  |  否 | 用户或应用 access_token |
{%- if user_verified_required %}
| bk_username   | string  |  否 | 当前用户用户名，应用免登录态验证白名单中的应用，用此字段指定当前用户 |
{%- endif %}
{%- endif %}
"""  # noqa


BKAPI_AUTHORIZATION_DESCRIPTION_EN = """
{%- if app_verified_required or user_verified_required %}
### Public Request Parameters

Public request parameters are parameters used to identify the application and user. If the cloud API requires authentication of the application or user, the request needs to carry these parameters in order to initiate the request properly. The public request parameters, which can be passed through the request header `X-Bkapi-Authorization`, have the value as a JSON formatted string.

**Example：** Use `curl` to carry the authorization header

```shell
curl -H 'X-Bkapi-Authorization: {"access_token": "your_token"}' "http://example.com/api"
```

**Example：** Use Python and the `requests` module

```python
import json
import requests

requests.get(
    'http://example.com/api',
    headers={
        'X-Bkapi-Authorization': json.dumps({'access_token': 'your_token'})
    },
)
```

The supported fields of the header `X-Bkapi-Authorization` are shown in the following table:

| Field  | Type | Required |  Description |
|-----------|------------|--------|------------|
{%- if app_verified_required %}
| bk_app_code   | string  |  No | App ID, can get from `Developer Center -> App Settings -> Basic Information -> Authentication Information`; *Gateway SDK added by default* |
| bk_app_secret | string  |  No | App Secret, can get from `Developer Center -> App Settings -> Basic Information -> Authentication Information`; *Gateway SDK added by default* |
{%- endif %}
| access_token  | string  |  No | User or App access_token |
{%- if user_verified_required %}
| bk_username   | string  |  No | Current user username, user verification exempted apps, use this field to specify the current user  |
{%- endif %}
{%- endif %}
"""  # noqa


BKAPI_AUTHORIZATION_DESCRIPTIONS = {
    LanguageCodeEnum.ZH_HANS.value: BKAPI_AUTHORIZATION_DESCRIPTION_ZH,
    LanguageCodeEnum.EN.value: BKAPI_AUTHORIZATION_DESCRIPTION_EN,
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
    LanguageCodeEnum.ZH_HANS.value: RESOURCE_URL_PART_ZH,
    LanguageCodeEnum.EN.value: RESOURCE_URL_PART_EN,
}
