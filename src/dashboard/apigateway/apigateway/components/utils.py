# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import copy
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.utils.translation import get_language

from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.request import gen_operation_tenant_header
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.utils.local import local

logger = logging.getLogger("component")


def gen_gateway_headers(
    user_credentials: Optional[UserCredentials] = None,
    with_operation_tenant_headers: bool = False,
) -> Dict[str, str]:
    """gen gateway headers while calling apigateway api

    Args:
        user_credentials (Optional[UserCredentials], optional): the user's credentials from request, including the bk_token and tenant_id. Defaults to None.
        with_operation_tenant_headers (bool, optional): add `system` as the X-Bk-Tenant-Id. Defaults to False. only works if the user_credentials is None!

    Returns:
        Dict[str, str]: header key values
    """
    bk_api_authorization = {
        "bk_app_code": settings.BK_APP_CODE,
        "bk_app_secret": settings.BK_APP_SECRET,
    }
    if user_credentials:
        bk_api_authorization.update(user_credentials.auth_dict())

    headers = {
        "Content-Type": "application/json",
        "X-Bkapi-Authorization": json.dumps(bk_api_authorization),
    }
    language = get_language()
    if language:
        headers["Accept-Language"] = language

    # if not user_credentials, then the with_operation_tenant_headers works
    if user_credentials:
        headers.update(user_credentials.tenant_dict())
    elif with_operation_tenant_headers:
        headers.update(gen_operation_tenant_header())

    return headers


def gen_ai_request_headers():
    bk_api_authorization = {
        "bk_app_code": settings.AI_APP_CODE,
        "bk_app_secret": settings.AI_APP_SECRET,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Bkapi-Authorization": json.dumps(bk_api_authorization),
    }
    language = get_language()
    if language:
        headers["Accept-Language"] = language

    return headers


def _remove_sensitive_info(info: Optional[Dict]) -> str:
    """
    去除敏感信息
    """
    if info is None:
        return ""

    data = copy.copy(info)
    sensitive_info_keys = ["bk_token", "bk_app_secret", "app_secret"]

    for key in sensitive_info_keys:
        if key in data:
            data[key] = data[key][:6] + "******"
    return str(data)


def do_legacy_blueking_http_request(
    component: str,
    http_func,
    url: str,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: Optional[int] = None,
    request_session=None,
) -> List | Dict:
    kwargs = {"url": url, "data": data, "headers": headers, "timeout": timeout, "request_session": request_session}

    ok, resp_data = http_func(**kwargs)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            component,
            http_func.__name__,
            url,
            _remove_sensitive_info(data),
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request {component} fail! "
            f"Request=[{http_func.__name__} {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )

    code = resp_data.get("code", -1)
    message = resp_data.get("message", "unknown")

    # code may be string or int, and login v1 the code is "00"
    try:
        code = int(code)
    except Exception:  # pylint: disable=broad-except
        pass
    if code in ("0", 0, "00"):
        return resp_data["data"]

    # the bkmonitorv3 return
    # {'result': True, 'code': 200, 'message': 'OK', 'data': {'metrics': [], 'series': []}}
    if code == 200 and resp_data.get("result"):
        return resp_data["data"]

    logger.error(
        "%s api error! %s %s, data: %s, request_id: %s, code: %s, message: %s",
        component,
        http_func.__name__,
        url,
        _remove_sensitive_info(data),
        local.request_id,
        code,
        message,
    )

    raise error_codes.REMOTE_REQUEST_ERROR.format(
        f"request {component} error! "
        f"Request=[{http_func.__name__} {urlparse(url).path} request_id={local.request_id}] "
        f"Response[code={code}, message={message}]"
    )


def do_blueking_http_request(
    component: str,
    http_func,
    url: str,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: Optional[int] = None,
    request_session=None,
) -> List | Dict:
    kwargs = {"url": url, "data": data, "headers": headers, "timeout": timeout, "request_session": request_session}

    ok, resp_data = http_func(**kwargs)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            component,
            http_func.__name__,
            url,
            _remove_sensitive_info(data),
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request {component} fail! "
            f"Request=[{http_func.__name__} {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )

    return resp_data["data"]
