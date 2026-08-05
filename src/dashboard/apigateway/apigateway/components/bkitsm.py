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
from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.conf import settings

from apigateway.utils.url import url_join

from .http import http_get, http_post
from .utils import do_blueking_http_request, gen_gateway_headers

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ItsmWorkflow:
    form_schema: Dict[str, Any]
    raw: Dict[str, Any]

    @classmethod
    def from_response_item(cls, item: Any):
        if not isinstance(item, dict):
            raise TypeError("invalid system_workflow_list response: results items must be objects")

        form_schema = item.get("form_schema") or {}
        if not isinstance(form_schema, dict):
            raise TypeError("invalid system_workflow_list response: form_schema must be an object")

        return cls(form_schema=form_schema, raw=item)


@dataclass(frozen=True)
class ItsmWorkflowList:
    count: int
    workflows: tuple[ItsmWorkflow, ...]
    raw: Dict[str, Any]

    @classmethod
    def empty(cls):
        return cls(count=0, workflows=(), raw={})

    @classmethod
    def from_response(cls, resp: Any):
        if not isinstance(resp, dict):
            raise TypeError("invalid system_workflow_list response: response must be an object")

        count = resp.get("count", 0)
        if not isinstance(count, int):
            raise TypeError("invalid system_workflow_list response: count must be an integer")

        results = resp.get("results")
        if not isinstance(results, list):
            raise TypeError("invalid system_workflow_list response: results must be a list")

        return cls(
            count=count,
            workflows=tuple(ItsmWorkflow.from_response_item(item) for item in results),
            raw=resp,
        )

    @property
    def is_registered(self) -> bool:
        return self.count > 0


@dataclass(frozen=True)
class ItsmFormModelUpdateResult:
    updated_field_keys: frozenset[str]
    raw: Any

    @classmethod
    def from_response(cls, resp: Any):
        if isinstance(resp, dict) and resp.get("result") is False:
            raise RuntimeError(f"update_form_model failed: {resp}")

        response_data = resp.get("data") if isinstance(resp, dict) and isinstance(resp.get("data"), dict) else resp
        updated_fields = (
            ((response_data or {}).get("meta") or {}).get("fields", {}) if isinstance(response_data, dict) else {}
        )
        if not updated_fields:
            raise RuntimeError(f"update_form_model response missing meta.fields: {resp}")
        if not isinstance(updated_fields, dict):
            raise TypeError("invalid update_form_model response: meta.fields must be an object")

        return cls(updated_field_keys=frozenset(updated_fields.keys()), raw=resp)


@dataclass(frozen=True)
class ItsmTicketProcessor:
    user_id: str
    processor_type: str
    raw: Dict[str, Any]

    @classmethod
    def from_response_item(cls, item: Any) -> Optional["ItsmTicketProcessor"]:
        if not isinstance(item, dict):
            return None

        processor_type = item.get("type")
        if processor_type != "user":
            return None

        user_id = item.get("id")
        if not isinstance(user_id, str) or not user_id.strip():
            return None

        return cls(user_id=user_id.strip(), processor_type=processor_type, raw=item)


@dataclass(frozen=True)
class ItsmTicketDetail:
    history_processors: tuple[ItsmTicketProcessor, ...]
    current_processors: tuple[ItsmTicketProcessor, ...]
    raw: Dict[str, Any]

    @classmethod
    def from_response(cls, resp: Any):
        if not isinstance(resp, dict):
            raise TypeError("invalid ticket item response: response must be an object")

        data = resp.get("data")
        response_data = data if isinstance(data, dict) else resp
        return cls(
            history_processors=cls._extract_processors(response_data.get("history_processors"), "history_processors"),
            current_processors=cls._extract_processors(response_data.get("current_processors"), "current_processors"),
            raw=resp,
        )

    @staticmethod
    def _extract_processors(processors: Any, field_name: str) -> tuple[ItsmTicketProcessor, ...]:
        if processors is None:
            return ()
        if not isinstance(processors, list):
            raise TypeError(f"invalid ticket item response: {field_name} must be a list")

        return tuple(
            processor
            for processor in (ItsmTicketProcessor.from_response_item(item) for item in processors)
            if processor is not None
        )

    @property
    def actual_approver(self) -> str:
        for processor in self.history_processors:
            return processor.user_id

        return ""


@dataclass(frozen=True)
class ItsmTicketSearchResult:
    count: int
    tickets: tuple[ItsmTicketDetail, ...]
    raw: Dict[str, Any]

    @classmethod
    def from_response(cls, resp: Any):
        if not isinstance(resp, dict):
            raise TypeError("invalid ticket_search_full_text_search response: response must be an object")

        response_data = resp.get("data")
        if not isinstance(response_data, dict):
            raise TypeError("invalid ticket_search_full_text_search response: data must be an object")

        results = response_data.get("results")
        if not isinstance(results, list):
            raise TypeError("invalid ticket_search_full_text_search response: results must be a list")

        count = response_data.get("count", len(results))
        if not isinstance(count, int):
            raise TypeError("invalid ticket_search_full_text_search response: count must be an integer")

        return cls(
            count=count,
            tickets=tuple(ItsmTicketDetail.from_response(item) for item in results),
            raw=resp,
        )

    @property
    def actual_approver(self) -> str:
        for ticket in self.tickets:
            if ticket.actual_approver:
                return ticket.actual_approver

        return ""


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

    resp = _call_bkitsm_api(
        http_get,
        "/api/v1/system_workflow/list/",
        data,
        more_headers=more_headers,
        timeout=settings.BK_ITSM4_API_TIMEOUT,
    )
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


def ticket_search_full_text_search(ticket_id: str, operator: Optional[str] = None) -> ItsmTicketSearchResult:
    """
    批量查询 ITSM 工单列表

    调用接口: ticket_search_full_text_search (POST)
    路径: /api/v1/ticket_search/full_text_search/
    """
    data = {
        "page": 1,
        "page_size": 10,
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
