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
from pydantic import BaseModel

from apigateway.utils.url import url_join

from .http import http_get, http_post
from .utils import do_blueking_http_request, gen_gateway_headers

logger = logging.getLogger(__name__)


class ItsmSystemNotFoundError(Exception):
    """ITSM system has not been registered yet."""


class ItsmWorkflow(BaseModel):
    form_schema: Dict[str, Any]


class ItsmWorkflowList(BaseModel):
    count: int
    results: list[ItsmWorkflow]

    @classmethod
    def empty(cls) -> "ItsmWorkflowList":
        return cls(count=0, results=[])

    @classmethod
    def from_response(cls, resp: Any) -> "ItsmWorkflowList":
        return cls.model_validate(resp)

    @property
    def workflows(self) -> list[ItsmWorkflow]:
        return self.results

    @property
    def is_registered(self) -> bool:
        return self.count > 0


class ItsmFormModelMeta(BaseModel):
    fields: Dict[str, Any]


class ItsmFormModelUpdateResult(BaseModel):
    meta: ItsmFormModelMeta

    @classmethod
    def from_response(cls, resp: Any) -> "ItsmFormModelUpdateResult":
        return cls.model_validate(resp)

    @property
    def updated_field_keys(self) -> frozenset[str]:
        return frozenset(self.meta.fields.keys())


class ItsmTicketProcessor(BaseModel):
    id: str
    type: str
    display: str = ""


class ItsmTicketItem(BaseModel):
    id: str
    history_processors: Optional[list[ItsmTicketProcessor]] = None

    @property
    def actual_approver(self) -> str:
        history_processors = [processor for processor in (self.history_processors or []) if processor.type == "user"]
        return history_processors[0].id if history_processors else ""


class ItsmTicketSearchResult(BaseModel):
    results: list[ItsmTicketItem]
    page: int = 1
    page_size: int = 10
    count: int

    @classmethod
    def from_response(cls, resp: Any) -> "ItsmTicketSearchResult":
        return cls.model_validate(resp)

    @property
    def actual_approver(self) -> str:
        approvers = [ticket.actual_approver for ticket in self.results if ticket.actual_approver]
        return approvers[0] if approvers else ""


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


def _system_workflow_list_http_get(system_id: str):
    def request(*args, **kwargs):
        ok, resp_data = http_get(*args, **kwargs)
        if not ok:
            response_data = resp_data.get("response_data") or {}
            try:
                code = int(response_data.get("code"))
            except TypeError, ValueError:
                code = None

            if resp_data.get("status_code") == 400 and code == 40000:
                raise ItsmSystemNotFoundError(f"ITSM system does not exist, system_id={system_id}")

        return ok, resp_data

    request.__name__ = http_get.__name__
    return request


def system_workflow_list(
    system_id: str,
    system_token: str = "",
    page: int = 1,
    page_size: int = 100,
) -> ItsmWorkflowList:
    """
    获取 ITSM 系统下的流程列表

    调用接口: system_workflow_list (GET)
    路径: /api/v1/system_workflow/list/

    系统尚未注册时 ITSM 会返回 HTTP 400 且 code=40000，按未注册（空列表）处理。
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

    try:
        resp = _call_bkitsm_api(
            _system_workflow_list_http_get(system_id),
            "/api/v1/system_workflow/list/",
            data,
            more_headers=more_headers,
            timeout=settings.BK_ITSM4_API_TIMEOUT,
        )
    except ItsmSystemNotFoundError:
        logger.info("ITSM system not found, treat as not registered, system_id=%s", system_id)
        return ItsmWorkflowList.empty()

    return ItsmWorkflowList.from_response(resp)


def update_form_model(
    key: str,
    name: str,
    meta: Dict[str, Any],
    desc: str = "",
    app_id: str = "",
    system_id: str = "",
) -> ItsmFormModelUpdateResult:
    """
    更新 ITSM 表单模型

    调用接口: form_models_update (POST)
    路径: /api/v1/form_models/update/
    """
    data: Dict[str, Any] = {
        "key": key,
        "name": name,
        "meta": meta,
    }
    if desc:
        data["desc"] = desc
    if app_id:
        data["app_id"] = app_id
    if system_id:
        data["system_id"] = system_id

    more_headers = {}
    if system_id and settings.BK_ITSM4_SYSTEM_TOKEN:
        more_headers["SYSTEM-TOKEN"] = settings.BK_ITSM4_SYSTEM_TOKEN

    resp = _call_bkitsm_api(
        http_post,
        "/api/v1/form_models/update/",
        data,
        more_headers=more_headers,
        timeout=settings.BK_ITSM4_API_TIMEOUT,
    )
    return ItsmFormModelUpdateResult.from_response(resp)


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


def get_ticket_by_id(ticket_id: str, operator: Optional[str] = None) -> ItsmTicketSearchResult:
    """
    按工单 ID 查询单条 ITSM 工单。

    因 /ticket/detail/ 暂无法返回 history_processors，先走搜索接口按 id__in 精确查询。
    调用接口: ticket_search_full_text_search (POST)
    路径: /api/v1/ticket_search/full_text_search/
    """
    data = {
        "page": 1,
        # 按单个 ticket_id 查询，只需返回一条
        "page_size": 1,
        "id__in": ticket_id,
        "operator": operator or settings.BK_ITSM4_QUERY_OPERATOR,
        "group_key": "all",
    }
    resp = _call_bkitsm_api(
        http_post,
        "/api/v1/ticket_search/full_text_search/",
        data,
        timeout=settings.BK_ITSM4_API_TIMEOUT,
    )
    return ItsmTicketSearchResult.from_response(resp)
