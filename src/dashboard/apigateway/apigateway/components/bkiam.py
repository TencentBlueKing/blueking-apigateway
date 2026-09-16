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
from typing import Any, Iterator, NotRequired, TypedDict, TypeVar

from django.conf import settings

from apigateway.utils.url import url_join

from .http import http_delete, http_get, http_post, http_put
from .utils import do_blueking_http_request, gen_gateway_headers

MAX_BATCH_SIZE = 20
DEFAULT_PAGE_SIZE = 100
REQUEST_TIMEOUT = 3
# 与 biz.iam.constants.BK_IAM_V4_SYSTEM_ID 保持一致；component 不能依赖 biz。
BK_IAM_V4_SYSTEM_ID = "bk_apigateway"
_T = TypeVar("_T")


class SubjectPayload(TypedDict):
    type: str
    id: str


class ResourcePayload(TypedDict):
    type: str
    id: str


class DirectAuthResourcePayload(TypedDict):
    id: str


class DirectAuthPayload(TypedDict):
    subject: SubjectPayload
    action_id: str
    resource: NotRequired[DirectAuthResourcePayload]


class SystemPayload(TypedDict):
    id: str
    name: str
    clients: list[str]
    description: NotRequired[str]
    managers: NotRequired[list[str]]
    callback_url: NotRequired[str]


class SystemUpdatePayload(TypedDict, total=False):
    name: str
    description: str
    managers: list[str]
    clients: list[str]
    callback_url: str


class ResourceTypePayload(TypedDict):
    id: str
    name: str
    ancestors: NotRequired[list[str]]


class ResourceTypeUpdatePayload(TypedDict, total=False):
    name: str
    ancestors: list[str]


class ActionPayload(TypedDict):
    id: str
    name: str
    resource_type_id: NotRequired[str]


class ActionUpdatePayload(TypedDict):
    name: str


class RoleActionPayload(TypedDict):
    id: str
    resource_type_id: NotRequired[str]


class RolePayload(TypedDict):
    id: str
    name: str
    actions: list[RoleActionPayload]
    description: NotRequired[str]


class RoleUpdatePayload(TypedDict, total=False):
    name: str
    description: str


class AuthorizationPayload(TypedDict):
    subject: SubjectPayload
    role_id: str
    expired_at: int
    related_resource_type_id: NotRequired[str]
    resources: NotRequired[list[ResourcePayload]]


class RevokeAuthorizationPayload(TypedDict):
    subject: SubjectPayload
    role_id: str
    related_resource_type_id: NotRequired[str]
    resources: NotRequired[list[ResourcePayload]]


class AuthorizationSubjectQueryPayload(TypedDict):
    role_id: str
    related_resource_type_id: NotRequired[str]
    resource: NotRequired[ResourcePayload]
    page: NotRequired[int]
    page_size: NotRequired[int]


class PaginationData(TypedDict):
    count: int
    results: list[dict[str, Any]]


class AuthorizationSubjectItem(TypedDict):
    id: str
    expired_at: int


class AuthorizationSubjectPage(TypedDict):
    count: int
    results: list[AuthorizationSubjectItem]


class BkIamNotFoundError(Exception):
    """IAM 系统尚未注册。"""


class BkIamParameterError(Exception):
    """本地请求参数不合法。"""


def _call_bkiam_api(http_func, path: str, data=None, more_headers=None, **kwargs):
    """
    统一调用权限中心 V4 网关 API。
    """
    headers = gen_gateway_headers()
    if more_headers:
        headers.update(more_headers)

    url = url_join(settings.BK_IAM_V4_API_URL, path)
    return do_blueking_http_request("bkiam", http_func, url, data, headers, REQUEST_TIMEOUT, **kwargs)


def _retrieve_system_http_get():
    """查询系统：HTTP 404 视为尚未注册。"""

    def request(*args, **kwargs):
        ok, resp_data = http_get(*args, **kwargs)
        if not ok and resp_data.get("status_code") == 404:
            raise BkIamNotFoundError(f"IAM system does not exist, system_id={BK_IAM_V4_SYSTEM_ID}")
        return ok, resp_data

    request.__name__ = http_get.__name__
    return request


def _batch(items):
    """批量接口本地校验条数，超过 MAX_BATCH_SIZE 直接拒绝。"""
    values = list(items)
    if len(values) > MAX_BATCH_SIZE:
        raise BkIamParameterError(f"at most {MAX_BATCH_SIZE} items")
    return values


def chunked(items: list[_T], size: int = MAX_BATCH_SIZE) -> Iterator[list[_T]]:
    """按固定大小切分顺序列表，保持原顺序。"""
    for offset in range(0, len(items), size):
        yield list(items[offset : offset + size])


def _validate_pagination_args(page: int, page_size: int) -> dict[str, int]:
    """分页参数校验，page_size 上限为 DEFAULT_PAGE_SIZE。"""
    if page < 1 or page_size < 1 or page_size > DEFAULT_PAGE_SIZE:
        raise BkIamParameterError(f"page_size between 1 and {DEFAULT_PAGE_SIZE}")
    return {"page": page, "page_size": page_size}


def _validate_authorization_resources(authorizations) -> None:
    """单条授权的 resources 数量不能超过批量上限。"""
    if any(len(authorization.get("resources", [])) > MAX_BATCH_SIZE for authorization in authorizations):
        raise BkIamParameterError(f"at most {MAX_BATCH_SIZE} resources per authorization")


def _authorization_subject_item(item: dict[str, Any]) -> AuthorizationSubjectItem:
    """把 IAM 原始 subject 收成用户 id + 过期时间。"""
    subject = item["subject"]
    if subject["type"] != "user":
        raise ValueError(f"IAM authorization subject type must be user, got {subject['type']!r}")
    return {"id": subject["id"], "expired_at": item["expired_at"]}


def retrieve_system() -> dict[str, Any]:
    """
    查询当前系统。系统不存在时抛 BkIamNotFoundError。

    调用接口: retrieve_system (GET)
    路径: /api/v1/open/rbac/model/systems/{system_id}/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/"
    return _call_bkiam_api(_retrieve_system_http_get(), path, {})


def create_system(system: SystemPayload) -> dict[str, Any]:
    """
    创建 IAM 系统。

    调用接口: create_system (POST)
    路径: /api/v1/open/rbac/model/systems/
    """
    path = "/api/v1/open/rbac/model/systems/"
    return _call_bkiam_api(http_post, path, system)


def update_system(system: SystemUpdatePayload) -> None:
    """
    更新 IAM 系统。

    调用接口: update_system (PUT)
    路径: /api/v1/open/rbac/model/systems/{system_id}/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/"
    _call_bkiam_api(http_put, path, system)


def list_resource_type(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PaginationData:
    """
    分页查询资源类型。

    调用接口: list_resource_type (GET)
    路径: /api/v1/open/rbac/model/systems/{system_id}/resource-types/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/resource-types/"
    params = _validate_pagination_args(page, page_size)
    return _call_bkiam_api(http_get, path, params)


def batch_create_resource_type(resource_types: list[ResourceTypePayload]) -> list[str]:
    """
    批量创建资源类型。

    调用接口: batch_create_resource_type (POST)
    路径: /api/v1/open/rbac/model/systems/{system_id}/resource-types/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/resource-types/"
    return _call_bkiam_api(http_post, path, _batch(resource_types))


def update_resource_type(resource_type_id: str, resource_type: ResourceTypeUpdatePayload) -> None:
    """
    更新资源类型。

    调用接口: update_resource_type (PUT)
    路径: /api/v1/open/rbac/model/systems/{system_id}/resource-types/{resource_type_id}/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/resource-types/{resource_type_id}/"
    _call_bkiam_api(http_put, path, resource_type)


def list_action(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PaginationData:
    """
    分页查询操作。

    调用接口: list_action (GET)
    路径: /api/v1/open/rbac/model/systems/{system_id}/actions/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/actions/"
    params = _validate_pagination_args(page, page_size)
    return _call_bkiam_api(http_get, path, params)


def batch_create_action(actions: list[ActionPayload]) -> list[str]:
    """
    批量创建操作。

    调用接口: batch_create_action (POST)
    路径: /api/v1/open/rbac/model/systems/{system_id}/actions/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/actions/"
    return _call_bkiam_api(http_post, path, _batch(actions))


def update_action(action_id: str, action: ActionUpdatePayload) -> None:
    """
    更新操作。

    调用接口: update_action (PUT)
    路径: /api/v1/open/rbac/model/systems/{system_id}/actions/{action_id}/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/actions/{action_id}/"
    _call_bkiam_api(http_put, path, action)


def list_role(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PaginationData:
    """
    分页查询角色。

    调用接口: list_role (GET)
    路径: /api/v1/open/rbac/model/systems/{system_id}/roles/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/roles/"
    params = _validate_pagination_args(page, page_size)
    return _call_bkiam_api(http_get, path, params)


def batch_create_role(roles: list[RolePayload]) -> list[str]:
    """
    批量创建角色。

    调用接口: batch_create_role (POST)
    路径: /api/v1/open/rbac/model/systems/{system_id}/roles/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/roles/"
    return _call_bkiam_api(http_post, path, _batch(roles))


def update_role(role_id: str, role: RoleUpdatePayload) -> None:
    """
    更新角色。

    调用接口: update_role (PUT)
    路径: /api/v1/open/rbac/model/systems/{system_id}/roles/{role_id}/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/roles/{role_id}/"
    _call_bkiam_api(http_put, path, role)


def batch_create_role_action(role_id: str, actions: list[RoleActionPayload]) -> list[str]:
    """
    批量为角色绑定操作。

    调用接口: batch_create_role_action (POST)
    路径: /api/v1/open/rbac/model/systems/{system_id}/roles/{role_id}/actions/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/roles/{role_id}/actions/"
    return _call_bkiam_api(http_post, path, _batch(actions))


def batch_delete_role_action(role_id: str, action_ids: list[str]) -> None:
    """
    批量解绑角色操作。

    调用接口: batch_delete_role_action (DELETE)
    路径: /api/v1/open/rbac/model/systems/{system_id}/roles/{role_id}/actions/
    """
    path = f"/api/v1/open/rbac/model/systems/{BK_IAM_V4_SYSTEM_ID}/roles/{role_id}/actions/"
    _call_bkiam_api(http_delete, path, None, params={"ids": ",".join(_batch(action_ids))})


def direct_auth(payload: DirectAuthPayload) -> bool:
    """
    鉴权：判断主体是否拥有指定操作。

    调用接口: direct_auth (POST)
    路径: /api/v1/open/rbac/authorization/systems/{system_id}/auth/
    """
    path = f"/api/v1/open/rbac/authorization/systems/{BK_IAM_V4_SYSTEM_ID}/auth/"
    data = _call_bkiam_api(http_post, path, payload)
    return data["allowed"]


def add_authorization(authorizations: list[AuthorizationPayload], operator: str) -> None:
    """
    批量授予角色授权。

    调用接口: add_authorization (POST)
    路径: /api/v1/open/rbac/mgmt/systems/{system_id}/authorizations/
    """
    payload = _batch(authorizations)
    _validate_authorization_resources(payload)
    path = f"/api/v1/open/rbac/mgmt/systems/{BK_IAM_V4_SYSTEM_ID}/authorizations/"
    _call_bkiam_api(http_post, path, payload, more_headers={"X-Bkiam-Operator": operator})


def revoke_authorization(authorizations: list[RevokeAuthorizationPayload], operator: str) -> None:
    """
    批量回收角色授权。

    调用接口: revoke_authorization (DELETE)
    路径: /api/v1/open/rbac/mgmt/systems/{system_id}/authorizations/
    """
    payload = _batch(authorizations)
    _validate_authorization_resources(payload)
    path = f"/api/v1/open/rbac/mgmt/systems/{BK_IAM_V4_SYSTEM_ID}/authorizations/"
    _call_bkiam_api(http_delete, path, payload, more_headers={"X-Bkiam-Operator": operator})


def list_authorization_subject(payload: AuthorizationSubjectQueryPayload) -> AuthorizationSubjectPage:
    """
    按角色和资源查询已授权主体。

    调用接口: list_authorization_subject (POST)
    路径: /api/v1/open/rbac/mgmt/systems/{system_id}/authorizations/query-subject/
    """
    _validate_pagination_args(payload.get("page", 1), payload.get("page_size", DEFAULT_PAGE_SIZE))
    path = f"/api/v1/open/rbac/mgmt/systems/{BK_IAM_V4_SYSTEM_ID}/authorizations/query-subject/"
    data = _call_bkiam_api(http_post, path, payload)
    return {
        "count": data["count"],
        "results": [_authorization_subject_item(item) for item in data["results"]],
    }


def iter_authorization_subjects(payload: AuthorizationSubjectQueryPayload) -> Iterator[AuthorizationSubjectItem]:
    """按页迭代已授权主体，分页循环由本组件封装。

    调用方只需传入查询条件（page/page_size 会被覆盖）。以第一页的 count 作为本次
    查询快照的数量上限；查询期间数据减少导致提前出现空页时，正常结束。
    """
    page_size = payload.get("page_size", DEFAULT_PAGE_SIZE)
    page = 1
    snapshot_count = 0
    fetched = 0
    while page == 1 or fetched < snapshot_count:
        query_payload: AuthorizationSubjectQueryPayload = {
            "role_id": payload["role_id"],
            "page": page,
            "page_size": page_size,
        }
        if "related_resource_type_id" in payload:
            query_payload["related_resource_type_id"] = payload["related_resource_type_id"]
        if "resource" in payload:
            query_payload["resource"] = payload["resource"]
        data = list_authorization_subject(query_payload)
        if page == 1:
            snapshot_count = data["count"]

        results = data["results"]
        if not results:
            return

        remaining = snapshot_count - fetched
        page_results = results[:remaining]
        for item in page_results:
            yield item

        fetched += len(page_results)
        page += 1
