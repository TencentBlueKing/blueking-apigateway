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
import json
import logging
from typing import Any, Dict, Optional

from django.conf import settings

from apigateway.utils.url import url_join

from .http import http_get, http_post
from .utils import do_blueking_http_request, gen_gateway_headers

logger = logging.getLogger(__name__)


def _call_bkitsm_api(
    http_func,
    path: str,
    data: Optional[Dict[str, Any]] = None,
    more_headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    keep_json_content_type: bool = True,
    **kwargs,
) -> Any:
    """
    统一调用 bk-itsm4 网关 API
    """
    headers = gen_gateway_headers(with_operation_tenant_headers=True)
    if not keep_json_content_type:
        headers.pop("Content-Type", None)
    if more_headers:
        headers.update(more_headers)

    url = url_join(settings.BK_ITSM4_URL_PREFIX, path)

    return do_blueking_http_request("bkitsm", http_func, url, data, headers, timeout, **kwargs)


def create_system(name: str, code: str, token: str, desc: str = "") -> Dict[str, Any]:
    """
    在 ITSM 中创建系统

    调用接口: system_create (POST)
    路径: /api/v1/system/create/
    """
    data = {
        "name": name,
        "code": code,
        "token": token,
    }
    if desc:
        data["desc"] = desc

    return _call_bkitsm_api(http_post, "/api/v1/system/create/", data, timeout=settings.BK_ITSM4_API_TIMEOUT)


def system_migrate(workflow_template: Dict[str, Any]) -> Dict[str, Any]:
    """
    在 ITSM 中通过模板导入系统初始化资源

    调用接口: system_migrate (POST)
    路径: /api/v1/system/migrate/
    """
    template_content = json.dumps(workflow_template, ensure_ascii=False, indent=2).encode("utf-8")

    return _call_bkitsm_api(
        http_post,
        "/api/v1/system/migrate/",
        data=None,
        timeout=180,
        keep_json_content_type=False,
        files={"file": template_content},
    )


def system_workflow_list(
    system_id: str,
    system_token: str = "",
    page: int = 1,
    page_size: int = 100,
) -> Dict[str, Any]:
    """
    获取 ITSM 系统下的流程列表

    调用接口: system_workflow_list (GET)
    路径: /api/v1/system_workflow/list/
    """
    data = {
        "system_id": system_id,
        "page": page,
        "page_size": page_size,
    }

    more_headers = {}
    if system_token:
        more_headers["SYSTEM-TOKEN"] = system_token
    elif settings.BK_ITSM4_SYSTEM_TOKEN:
        more_headers["SYSTEM-TOKEN"] = settings.BK_ITSM4_SYSTEM_TOKEN

    return _call_bkitsm_api(
        http_get,
        "/api/v1/system_workflow/list/",
        data,
        more_headers=more_headers,
        timeout=settings.BK_ITSM4_API_TIMEOUT,
    )


def create_system_workflow(
    system_id: str,
    name: str,
    form_schema: Dict[str, Any],
    portal_id: str = "DEFAULT",
    desc: str = "",
    workflow_category: str = "",
    predefined_approver: Optional[Dict[str, Any]] = None,
    system_token: str = "",
) -> Dict[str, Any]:
    """
    在 ITSM 中创建系统流程

    调用接口: system_workflow_create (POST)
    路径: /api/v1/system_workflow/create/
    """
    data: Dict[str, Any] = {
        "system_id": system_id,
        "name": name,
        "form_schema": form_schema,
        "portal_id": portal_id,
    }
    if desc:
        data["desc"] = desc
    if workflow_category:
        data["workflow_category"] = workflow_category
    if predefined_approver:
        data["predefined_approver"] = predefined_approver

    more_headers = {}
    if system_token:
        more_headers["SYSTEM-TOKEN"] = system_token

    return _call_bkitsm_api(
        http_post,
        "/api/v1/system_workflow/create/",
        data,
        more_headers=more_headers,
        timeout=settings.BK_ITSM4_API_TIMEOUT,
    )


def create_ticket(
    workflow_key: str,
    form_data: Dict[str, Any],
    operator: str = "",
    callback_url: str = "",
    callback_token: str = "",
    system_id: str = "",
    system_token: str = "",
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    在 ITSM 中创建工单

    调用接口: ticket_create (POST)
    路径: /api/v1/ticket/create/
    """
    data: Dict[str, Any] = {
        "workflow_key": workflow_key,
        "form_data": form_data,
    }
    if operator:
        data["operator"] = operator
    if callback_url:
        data["callback_url"] = callback_url
    if callback_token:
        data["callback_token"] = callback_token
    if system_id:
        data["system_id"] = system_id
    if options:
        data["options"] = options

    more_headers = {}
    if system_token:
        more_headers["SYSTEM-TOKEN"] = system_token
    elif system_id and settings.BK_ITSM4_SYSTEM_TOKEN:
        more_headers["SYSTEM-TOKEN"] = settings.BK_ITSM4_SYSTEM_TOKEN

    return _call_bkitsm_api(
        http_post,
        "/api/v1/ticket/create/",
        data,
        more_headers=more_headers,
        timeout=settings.BK_ITSM4_API_TIMEOUT,
    )
