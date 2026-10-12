# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from django.conf import settings

from apigateway.apps.support.constants import DocLanguageEnum


class APIDocTypeEnum(StructuredEnum):
    MARKDOWN = EnumField("markdown")


BKAPI_AUTHORIZATION_DESCRIPTION_ZH = """
{%- if verified_app_required or verified_user_required or access_token_header or username_header_required %}
### 公共请求参数

公共请求参数是用于标识应用和用户的参数，如果云 API 接口需要认证应用或用户，则请求时需要携带这些参数，才能正常发起请求。公共请求参数，可通过请求头 `{{ access_token_header or "X-Bkapi-Authorization" }}` 传递，{% if access_token_header %}值为 `{{ access_token_example }}`{% else %}值为 JSON 格式字符串{% endif %}。{%- if docs_urls.USE_GATEWAY_API %}详情请查看 [调用网关 API]({{ docs_urls.USE_GATEWAY_API }}){%- endif %}
{%- if access_token_header and allow_fallback %}

也支持通过 `X-Bkapi-Authorization` 请求头传递认证信息。
{%- endif %}

**示例：** 使用 curl 命令，请求时携带认证请求头

```shell
{%- if access_token_header %}
curl -H '{{ access_token_header }}: {{ access_token_example }}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required and verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y"}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif username_header_required %}
curl -H 'X-Bk-Username: {username}' "http://example.com/api"
{%- endif %}
```

**示例：** 使用 Python 语言和 requests 模块

```python
import json
import requests

requests.get(
    "http://example.com/api",
    headers={
        {%- if access_token_header %}
        "{{ access_token_header }}": "{{ access_token_example }}",
        {%- elif verified_app_required and verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}){% if username_header_required %},{% endif %}
        {%- elif verified_app_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y"}){% if username_header_required %},{% endif %}
        {%- elif verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}){% if username_header_required %},{% endif %}
        {%- endif %}
        {%- if username_header_required %}
        "X-Bk-Username": "{username}",
        {%- endif %}
    },
)
```
{%- if access_token_header or username_header_required %}

请求头参数如下表所示：

| 字段  | 类型 | 必选 |  描述 |
|-----------|------------|--------|------------|
{%- if access_token_header %}
| {{ access_token_header }} | string | {% if allow_fallback %}二选一{% else %}是{% endif %} | 用户 access_token，格式为 `{{ access_token_example }}` |
{%- if allow_fallback %}
| X-Bkapi-Authorization | string | 二选一 | JSON 格式的认证信息 |
{%- endif %}
{%- endif %}
{%- if username_header_required %}
| X-Bk-Username | string | 是 | 请求头，调用方用户名，不能为空 |
{%- endif %}
{%- endif %}
{%- if (not access_token_header or allow_fallback) and (verified_app_required or verified_user_required) %}

`X-Bkapi-Authorization` 请求头所支持的全部字段如下表所示：

| 字段  | 类型 | 必选 |  描述 |
|-----------|------------|--------|------------|
{%- if verified_app_required %}
| bk_app_code   | string  |  是 | 应用 ID，可以通过`蓝鲸开发者中心 -> 应用设置 -> 基本信息 -> 密钥信息`获取；*网关 SDK 默认已添加* |
| bk_app_secret | string  |  是 | 安全秘钥，可以通过`蓝鲸开发者中心 -> 应用设置 -> 基本信息 -> 密钥信息`获取；*网关 SDK 默认已添加* |
{%- endif %}
{%- if verified_user_required %}
| {{ settings.BK_LOGIN_TICKET_KEY }}      | string  |  否 | 用户登录态，用于认证用户；登录蓝鲸，对应 Cookies 中 {{ settings.BK_LOGIN_TICKET_KEY }} 字段的值 |
{%- endif %}
{%- if verified_app_required and verified_user_required %}
| access_token  | string  |  否 | 用户 access_token{%- if docs_urls.ACCESS_TOKEN_API %}，详情参考 [AccessToken API]({{ docs_urls.ACCESS_TOKEN_API }}){%- endif %}；提供 access_token 时，不需要再提供 bk_app_code/bk_app_secret/{{ settings.BK_LOGIN_TICKET_KEY }} |
{%- endif %}
{%- endif %}
{%- endif %}
"""  # noqa


BKAPI_AUTHORIZATION_DESCRIPTION_ZH_MULTI_TENANT = """
{%- if verified_app_required or verified_user_required or access_token_header or username_header_required %}
### 公共请求参数

公共请求参数是用于标识租户、应用和用户的参数，如果云 API 接口需要识别租户，认证应用或用户，则请求时需要携带这些参数，才能正常发起请求。

公共请求参数包括认证参数和租户参数
- 认证参数，可通过请求头 `{{ access_token_header or "X-Bkapi-Authorization" }}` 传递，{% if access_token_header %}值为 `{{ access_token_example }}`{% else %}值为 JSON 格式字符串{% endif %}。{%- if docs_urls.USE_GATEWAY_API %}详情请查看 [调用网关 API]({{ docs_urls.USE_GATEWAY_API }}){%- endif %}
- 租户参数，可通过请求头 `X-Bk-Tenant-Id` 传递，如果应用为单租户应用，值为应用所属租户 ID, 如果应用为全租户应用，必须指定租户 ID。
{%- if access_token_header and allow_fallback %}

也支持通过 `X-Bkapi-Authorization` 请求头传递认证信息。
{%- endif %}

**示例：** 使用 curl 命令，请求时携带认证请求头和租户头

```shell
{%- if access_token_header %}
curl -H '{{ access_token_header }}: {{ access_token_example }}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required and verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y"}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif username_header_required %}
curl -H 'X-Bk-Username: {username}' "http://example.com/api"
{%- endif %}
```

**示例：** 使用 Python 语言和 requests 模块

```python
import json
import requests

requests.get(
    "http://example.com/api",
    headers={
        {%- if access_token_header %}
        "{{ access_token_header }}": "{{ access_token_example }}",
        {%- elif verified_app_required and verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}),
        {%- elif verified_app_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y"}),
        {%- elif verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}),
        {%- endif %}
        {%- if username_header_required %}
        "X-Bk-Username": "{username}",
        {%- endif %}
        {%- if verified_app_required or verified_user_required or access_token_header %}
        "X-Bk-Tenant-Id": "your_app_tenant_id"
        {%- endif %}
    },
)
```
{%- if access_token_header or username_header_required or verified_app_required or verified_user_required %}

请求头参数如下表所示：

| 字段  | 类型 | 必选 |  描述 |
|-----------|------------|--------|------------|
{%- if access_token_header %}
| {{ access_token_header }} | string | {% if allow_fallback %}二选一{% else %}是{% endif %} | 用户 access_token，格式为 `{{ access_token_example }}` |
{%- if allow_fallback %}
| X-Bkapi-Authorization | string | 二选一 | JSON 格式的认证信息 |
{%- endif %}
{%- endif %}
{%- if username_header_required %}
| X-Bk-Username | string | 是 | 请求头，调用方用户名，不能为空 |
{%- endif %}
{%- if verified_app_required or verified_user_required or access_token_header %}
| X-Bk-Tenant-Id | string | 是 | 租户 ID，单租户应用使用所属租户，全租户应用指定目标租户 |
{%- endif %}
{%- endif %}
{%- if (not access_token_header or allow_fallback) and (verified_app_required or verified_user_required) %}

`X-Bkapi-Authorization` 请求头所支持的全部字段如下表所示：

| 字段  | 类型 | 必选 |  描述 |
|-----------|------------|--------|------------|
{%- if verified_app_required %}
| bk_app_code   | string  |  是 | 应用 ID，可以通过`蓝鲸开发者中心 -> 应用设置 -> 基本信息 -> 密钥信息`获取；*网关 SDK 默认已添加* |
| bk_app_secret | string  |  是 | 安全秘钥，可以通过`蓝鲸开发者中心 -> 应用设置 -> 基本信息 -> 密钥信息`获取；*网关 SDK 默认已添加* |
{%- endif %}
{%- if verified_user_required %}
| {{ settings.BK_LOGIN_TICKET_KEY }}      | string  |  否 | 用户登录态，用于认证用户；登录蓝鲸，对应 Cookies 中 {{ settings.BK_LOGIN_TICKET_KEY }} 字段的值 |
{%- endif %}
{%- if verified_app_required and verified_user_required %}
| access_token  | string  |  否 | 用户 access_token{%- if docs_urls.ACCESS_TOKEN_API %}，详情参考 [AccessToken API]({{ docs_urls.ACCESS_TOKEN_API }}){%- endif %}；提供 access_token 时，不需要再提供 bk_app_code/bk_app_secret/{{ settings.BK_LOGIN_TICKET_KEY }} |
{%- endif %}
{%- endif %}
{%- endif %}
"""  # noqa

BKAPI_AUTHORIZATION_DESCRIPTION_EN = """
{%- if verified_app_required or verified_user_required or access_token_header or username_header_required %}
### Public Request Parameters

Public request parameters are parameters used to identify the application and user. If the cloud API requires authentication of the application or user, the request needs to carry these parameters in order to initiate the request properly. The public request parameters, which can be passed through the request header `{{ access_token_header or "X-Bkapi-Authorization" }}`, have the value {% if access_token_header %}`{{ access_token_example }}`{% else %}as a JSON formatted string{% endif %}. For more details see {%- if docs_urls.USE_GATEWAY_API %}[Call Gateway API]({{ docs_urls.USE_GATEWAY_API }}){%- endif %}
{%- if access_token_header and allow_fallback %}

You can also pass authentication credentials through the `X-Bkapi-Authorization` header.
{%- endif %}

**Example：** Use `curl` to carry the authorization header

```shell
{%- if access_token_header %}
curl -H '{{ access_token_header }}: {{ access_token_example }}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required and verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y"}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif username_header_required %}
curl -H 'X-Bk-Username: {username}' "http://example.com/api"
{%- endif %}
```

**Example：** Use Python and the `requests` module

```python
import json
import requests

requests.get(
    "http://example.com/api",
    headers={
        {%- if access_token_header %}
        "{{ access_token_header }}": "{{ access_token_example }}",
        {%- elif verified_app_required and verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}){% if username_header_required %},{% endif %}
        {%- elif verified_app_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y"}){% if username_header_required %},{% endif %}
        {%- elif verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}){% if username_header_required %},{% endif %}
        {%- endif %}
        {%- if username_header_required %}
        "X-Bk-Username": "{username}",
        {%- endif %}
    },
)
```
{%- if access_token_header or username_header_required %}

The request header parameters are shown in the following table:

| Field  | Type | Required |  Description |
|-----------|------------|--------|------------|
{%- if access_token_header %}
| {{ access_token_header }} | string | {% if allow_fallback %}Either one{% else %}Yes{% endif %} | User access_token, in the format `{{ access_token_example }}` |
{%- if allow_fallback %}
| X-Bkapi-Authorization | string | Either one | Authentication credentials in JSON format |
{%- endif %}
{%- endif %}
{%- if username_header_required %}
| X-Bk-Username | string | Yes | Request header, caller username. Must not be empty |
{%- endif %}
{%- endif %}
{%- if (not access_token_header or allow_fallback) and (verified_app_required or verified_user_required) %}

The supported fields of the header `X-Bkapi-Authorization` are shown in the following table:

| Field  | Type | Required |  Description |
|-----------|------------|--------|------------|
{%- if verified_app_required %}
| bk_app_code   | string  |  Yes | App ID, can get from `Developer Center -> App Settings -> Basic Information -> Secret Information`; *Gateway SDK added by default* |
| bk_app_secret | string  |  Yes | App Secret, can get from `Developer Center -> App Settings -> Basic Information -> Secret Information`; *Gateway SDK added by default* |
{%- endif %}
{%- if verified_user_required %}
| {{ settings.BK_LOGIN_TICKET_KEY }}      | string  |  No | User login token, used to authenticate user; login to BlueKing, corresponding to the value of the {{ settings.BK_LOGIN_TICKET_KEY }} field in Cookies |
{%- endif %}
{%- if verified_app_required and verified_user_required %}
| access_token  | string  |  No | User access_token{%- if docs_urls.ACCESS_TOKEN_API %}, details [AccessToken API]({{ docs_urls.ACCESS_TOKEN_API }}){%- endif %}; when providing access_token, there is no need to provide bk_app_code/bk_app_secret/{{ settings.BK_LOGIN_TICKET_KEY }} |
{%- endif %}
{%- endif %}
{%- endif %}
"""  # noqa

BKAPI_AUTHORIZATION_DESCRIPTION_EN_MULTI_TENANT = """
{%- if verified_app_required or verified_user_required or access_token_header or username_header_required %}
### Public Request Parameters

Public request parameters are parameters used to identify the tenant, application, and user. If the cloud API requires identifying the tenant, authenticating the application or user, the request needs to carry these parameters in order to initiate the request properly.

Public request parameters include authentication parameters and tenant parameters:
- Authentication parameters can be passed through the request header `{{ access_token_header or "X-Bkapi-Authorization" }}`, with the value {% if access_token_header %}`{{ access_token_example }}`{% else %}as a JSON formatted string{% endif %}. For more details see {%- if docs_urls.USE_GATEWAY_API %}[Call Gateway API]({{ docs_urls.USE_GATEWAY_API }}){%- endif %}.
- Tenant parameters can be passed through the request header `X-Bk-Tenant-Id`. If the application is a single-tenant application, the value is the tenant ID to which the application belongs. If the application is a multi-tenant application, the tenant ID must be specified.

{%- if access_token_header and allow_fallback %}

You can also pass authentication credentials through the `X-Bkapi-Authorization` header.
{%- endif %}

**Example：** Use `curl` to carry the authorization header

```shell
{%- if access_token_header %}
curl -H '{{ access_token_header }}: {{ access_token_example }}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required and verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_app_required %}
curl -H 'X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y"}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif verified_user_required %}
curl -H 'X-Bkapi-Authorization: {"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}' -H 'X-Bk-Tenant-Id: your_app_tenant_id'{% if username_header_required %} -H 'X-Bk-Username: {username}'{% endif %} "http://example.com/api"
{%- elif username_header_required %}
curl -H 'X-Bk-Username: {username}' "http://example.com/api"
{%- endif %}
```

**Example：** Use Python and the `requests` module

```python
import json
import requests

requests.get(
    "http://example.com/api",
    headers={
        {%- if access_token_header %}
        "{{ access_token_header }}": "{{ access_token_example }}",
        {%- elif verified_app_required and verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y", "{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}),
        {%- elif verified_app_required %}
        "X-Bkapi-Authorization": json.dumps({"bk_app_code": "x", "bk_app_secret": "y"}),
        {%- elif verified_user_required %}
        "X-Bkapi-Authorization": json.dumps({"{{ settings.BK_LOGIN_TICKET_KEY }}": "z"}),
        {%- endif %}
        {%- if username_header_required %}
        "X-Bk-Username": "{username}",
        {%- endif %}
        {%- if verified_app_required or verified_user_required or access_token_header %}
        "X-Bk-Tenant-Id": "your_app_tenant_id"
        {%- endif %}
    },
)
```
{%- if access_token_header or username_header_required or verified_app_required or verified_user_required %}

The request header parameters are shown in the following table:

| Field  | Type | Required |  Description |
|-----------|------------|--------|------------|
{%- if access_token_header %}
| {{ access_token_header }} | string | {% if allow_fallback %}Either one{% else %}Yes{% endif %} | User access_token, in the format `{{ access_token_example }}` |
{%- if allow_fallback %}
| X-Bkapi-Authorization | string | Either one | Authentication credentials in JSON format |
{%- endif %}
{%- endif %}
{%- if username_header_required %}
| X-Bk-Username | string | Yes | Request header, caller username. Must not be empty |
{%- endif %}
{%- if verified_app_required or verified_user_required or access_token_header %}
| X-Bk-Tenant-Id | string | Yes | Tenant ID: use the application's tenant for single-tenant apps, or specify the target tenant for multi-tenant apps |
{%- endif %}
{%- endif %}
{%- if (not access_token_header or allow_fallback) and (verified_app_required or verified_user_required) %}

The supported fields of the header `X-Bkapi-Authorization` are shown in the following table:

| Field  | Type | Required |  Description |
|-----------|------------|--------|------------|
{%- if verified_app_required %}
| bk_app_code   | string  |  Yes | App ID, can get from `Developer Center -> App Settings -> Basic Information -> Secret Information`; *Gateway SDK added by default* |
| bk_app_secret | string  |  Yes | App Secret, can get from `Developer Center -> App Settings -> Basic Information -> Secret Information`; *Gateway SDK added by default* |
{%- endif %}
{%- if verified_user_required %}
| {{ settings.BK_LOGIN_TICKET_KEY }}      | string  |  No | User login token, used to authenticate user; login to BlueKing, corresponding to the value of the {{ settings.BK_LOGIN_TICKET_KEY }} field in Cookies |
{%- endif %}
{%- if verified_app_required and verified_user_required %}
| access_token  | string  |  No | User access_token{%- if docs_urls.ACCESS_TOKEN_API %}, details [AccessToken API]({{ docs_urls.ACCESS_TOKEN_API }}){%- endif %}; when providing access_token, there is no need to provide bk_app_code/bk_app_secret/{{ settings.BK_LOGIN_TICKET_KEY }} |
{%- endif %}
{%- endif %}
{%- endif %}
"""  # noqa

if settings.ENABLE_MULTI_TENANT_MODE:
    BKAPI_AUTHORIZATION_DESCRIPTIONS = {
        DocLanguageEnum.ZH.value: BKAPI_AUTHORIZATION_DESCRIPTION_ZH_MULTI_TENANT,
        DocLanguageEnum.EN.value: BKAPI_AUTHORIZATION_DESCRIPTION_EN_MULTI_TENANT,
    }
else:
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
