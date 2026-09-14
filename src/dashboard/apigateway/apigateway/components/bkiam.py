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
from __future__ import annotations

from typing import TYPE_CHECKING, Any, NotRequired, TypedDict, cast

from django.conf import settings

from apigateway.components.http import http_delete, http_get, http_post, http_put
from apigateway.components.utils import gen_gateway_headers

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

MAX_BATCH_SIZE = 20
DEFAULT_PAGE_SIZE = 100

SYSTEMS_PATH = "/api/v1/open/rbac/model/systems/"
SYSTEM_PATH = "/api/v1/open/rbac/model/systems/{system_id}/"
RESOURCE_TYPES_PATH = "/api/v1/open/rbac/model/systems/{system_id}/resource-types/"
RESOURCE_TYPE_PATH = RESOURCE_TYPES_PATH + "{resource_type_id}/"
ACTIONS_PATH = "/api/v1/open/rbac/model/systems/{system_id}/actions/"
ACTION_PATH = ACTIONS_PATH + "{action_id}/"
ROLES_PATH = "/api/v1/open/rbac/model/systems/{system_id}/roles/"
ROLE_PATH = ROLES_PATH + "{role_id}/"
ROLE_ACTIONS_PATH = ROLE_PATH + "actions/"
DIRECT_AUTH_PATH = "/api/v1/open/rbac/authorization/systems/{system_id}/auth/"
AUTHORIZATIONS_PATH = "/api/v1/open/rbac/mgmt/systems/{system_id}/authorizations/"
AUTHORIZATION_SUBJECTS_PATH = AUTHORIZATIONS_PATH + "query-subject/"


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


class BkIamError(Exception):
    def __init__(
        self,
        message: str,
        *,
        operation: str,
        status_code: int | None = None,
        response_data: Any = None,
    ):
        super().__init__(message)
        self.operation = operation
        self.status_code = status_code
        self.response_data = response_data


class BkIamUnavailableError(BkIamError):
    pass


class BkIamNotFoundError(BkIamError):
    pass


class BkIamParameterError(BkIamError):
    pass


def _url(path: str) -> str:
    return f"{settings.BK_IAM_V4_API_URL.rstrip('/')}{path}"


def _system_path(path: str, **kwargs: str) -> str:
    return path.format(system_id=settings.BK_IAM_V4_SYSTEM_ID, **kwargs)


def _timeout() -> tuple[float, float]:
    return settings.BK_IAM_V4_CONNECT_TIMEOUT, settings.BK_IAM_V4_READ_TIMEOUT


def _raise_http_error(operation: str, response: Any, *, not_found_is_missing: bool = False) -> None:
    if not isinstance(response, dict):
        raise BkIamUnavailableError(
            f"bkiam {operation} transport failure",
            operation=operation,
            response_data=response,
        )

    status_code = response.get("status_code")
    if status_code is not None and (not isinstance(status_code, int) or isinstance(status_code, bool)):
        raise BkIamUnavailableError(
            f"bkiam {operation} returned an invalid status code",
            operation=operation,
            response_data=response,
        )
    response_data = response.get("response_data")
    message = f"bkiam {operation} request failed"
    if status_code == 404 and not_found_is_missing:
        raise BkIamNotFoundError(
            message,
            operation=operation,
            status_code=status_code,
            response_data=response_data,
        )
    if status_code == 400:
        raise BkIamParameterError(
            message,
            operation=operation,
            status_code=status_code,
            response_data=response_data,
        )
    if status_code is None or status_code in {401, 403, 404, 429} or status_code >= 500:
        raise BkIamUnavailableError(
            message,
            operation=operation,
            status_code=status_code,
            response_data=response_data,
        )
    raise BkIamError(
        message,
        operation=operation,
        status_code=status_code,
        response_data=response_data,
    )


def _request(
    operation: str,
    http_func: Callable[..., tuple[bool, Any]],
    path: str,
    data: dict[str, Any] | list[Any] | None = None,
    *,
    operator: str | None = None,
    expect_data: bool = True,
    not_found_is_missing: bool = False,
    **kwargs: Any,
) -> Any:
    headers = gen_gateway_headers()
    if operator is not None:
        headers["X-Bkiam-Operator"] = operator

    try:
        ok, response = http_func(
            url=_url(path),
            data=data,
            headers=headers,
            timeout=_timeout(),
            **kwargs,
        )
    except ValueError as exc:
        raise BkIamUnavailableError(
            f"bkiam {operation} returned malformed JSON",
            operation=operation,
        ) from exc
    if not ok:
        _raise_http_error(operation, response, not_found_is_missing=not_found_is_missing)
    if not isinstance(response, dict):
        raise BkIamUnavailableError(
            f"bkiam {operation} returned a malformed response",
            operation=operation,
            response_data=response,
        )
    if not expect_data:
        return None
    if "data" not in response:
        raise BkIamUnavailableError(
            f"bkiam {operation} response has no data",
            operation=operation,
            response_data=response,
        )
    return response["data"]


def _require_type(operation: str, data: Any, expected_type: type) -> Any:
    if not isinstance(data, expected_type):
        raise BkIamUnavailableError(
            f"bkiam {operation} returned invalid data",
            operation=operation,
            response_data=data,
        )
    return data


def _require_page(operation: str, data: Any) -> PaginationData:
    _require_type(operation, data, dict)
    if (
        not isinstance(data.get("count"), int)
        or isinstance(data.get("count"), bool)
        or not isinstance(data.get("results"), list)
    ):
        raise BkIamUnavailableError(
            f"bkiam {operation} returned invalid pagination data",
            operation=operation,
            response_data=data,
        )
    return cast("PaginationData", data)


def _batch(items: Sequence[Any], operation: str) -> list[Any]:
    values = list(items)
    if len(values) > MAX_BATCH_SIZE:
        raise BkIamParameterError(
            f"bkiam {operation} accepts at most {MAX_BATCH_SIZE} items",
            operation=operation,
        )
    return values


def _page_query(operation: str, page: int, page_size: int) -> dict[str, int]:
    if page < 1 or page_size < 1 or page_size > DEFAULT_PAGE_SIZE:
        raise BkIamParameterError(
            f"bkiam {operation} requires page >= 1 and page_size between 1 and {DEFAULT_PAGE_SIZE}",
            operation=operation,
        )
    return {"page": page, "page_size": page_size}


def _validate_authorization_resources(
    authorizations: Sequence[AuthorizationPayload | RevokeAuthorizationPayload],
    operation: str,
) -> None:
    if any(len(authorization.get("resources", [])) > MAX_BATCH_SIZE for authorization in authorizations):
        raise BkIamParameterError(
            f"bkiam {operation} accepts at most {MAX_BATCH_SIZE} resources per authorization",
            operation=operation,
        )


def retrieve_system() -> dict[str, Any]:
    operation = "retrieve_system"
    data = _request(operation, http_get, _system_path(SYSTEM_PATH), {}, not_found_is_missing=True)
    return cast("dict[str, Any]", _require_type(operation, data, dict))


def create_system(system: SystemPayload) -> dict[str, Any]:
    operation = "create_system"
    data = _request(operation, http_post, SYSTEMS_PATH, cast("dict[str, Any]", system))
    return cast("dict[str, Any]", _require_type(operation, data, dict))


def update_system(system: SystemUpdatePayload) -> None:
    _request(
        "update_system",
        http_put,
        _system_path(SYSTEM_PATH),
        cast("dict[str, Any]", system),
        expect_data=False,
    )


def list_resource_type(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PaginationData:
    operation = "list_resource_type"
    data = _request(
        operation,
        http_get,
        _system_path(RESOURCE_TYPES_PATH),
        _page_query(operation, page, page_size),
    )
    return _require_page(operation, data)


def batch_create_resource_type(resource_types: Sequence[ResourceTypePayload]) -> list[str]:
    operation = "batch_create_resource_type"
    data = _request(operation, http_post, _system_path(RESOURCE_TYPES_PATH), _batch(resource_types, operation))
    return cast("list[str]", _require_type(operation, data, list))


def update_resource_type(resource_type_id: str, resource_type: ResourceTypeUpdatePayload) -> None:
    _request(
        "update_resource_type",
        http_put,
        _system_path(RESOURCE_TYPE_PATH, resource_type_id=resource_type_id),
        cast("dict[str, Any]", resource_type),
        expect_data=False,
    )


def list_action(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PaginationData:
    operation = "list_action"
    data = _request(
        operation,
        http_get,
        _system_path(ACTIONS_PATH),
        _page_query(operation, page, page_size),
    )
    return _require_page(operation, data)


def batch_create_action(actions: Sequence[ActionPayload]) -> list[str]:
    operation = "batch_create_action"
    data = _request(operation, http_post, _system_path(ACTIONS_PATH), _batch(actions, operation))
    return cast("list[str]", _require_type(operation, data, list))


def update_action(action_id: str, action: ActionUpdatePayload) -> None:
    _request(
        "update_action",
        http_put,
        _system_path(ACTION_PATH, action_id=action_id),
        cast("dict[str, Any]", action),
        expect_data=False,
    )


def list_role(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PaginationData:
    operation = "list_role"
    data = _request(
        operation,
        http_get,
        _system_path(ROLES_PATH),
        _page_query(operation, page, page_size),
    )
    return _require_page(operation, data)


def batch_create_role(roles: Sequence[RolePayload]) -> list[str]:
    operation = "batch_create_role"
    data = _request(operation, http_post, _system_path(ROLES_PATH), _batch(roles, operation))
    return cast("list[str]", _require_type(operation, data, list))


def update_role(role_id: str, role: RoleUpdatePayload) -> None:
    _request(
        "update_role",
        http_put,
        _system_path(ROLE_PATH, role_id=role_id),
        cast("dict[str, Any]", role),
        expect_data=False,
    )


def batch_create_role_action(role_id: str, actions: Sequence[RoleActionPayload]) -> list[str]:
    operation = "batch_create_role_action"
    data = _request(
        operation,
        http_post,
        _system_path(ROLE_ACTIONS_PATH, role_id=role_id),
        _batch(actions, operation),
    )
    return cast("list[str]", _require_type(operation, data, list))


def batch_delete_role_action(role_id: str, action_ids: Sequence[str]) -> None:
    operation = "batch_delete_role_action"
    ids = _batch(action_ids, operation)
    _request(
        operation,
        http_delete,
        _system_path(ROLE_ACTIONS_PATH, role_id=role_id),
        None,
        expect_data=False,
        params={"ids": ",".join(ids)},
    )


def direct_auth(payload: DirectAuthPayload) -> bool:
    operation = "direct_auth"
    data = _request(
        operation,
        http_post,
        _system_path(DIRECT_AUTH_PATH),
        cast("dict[str, Any]", payload),
    )
    if not isinstance(data, dict) or type(data.get("allowed")) is not bool:
        raise BkIamUnavailableError(
            "bkiam direct_auth returned invalid allowed value",
            operation=operation,
            response_data=data,
        )
    return data["allowed"]


def add_authorization(authorizations: Sequence[AuthorizationPayload], operator: str) -> None:
    operation = "add_authorization"
    payload = cast("list[AuthorizationPayload]", _batch(authorizations, operation))
    _validate_authorization_resources(payload, operation)
    _request(
        operation,
        http_post,
        _system_path(AUTHORIZATIONS_PATH),
        cast("list[Any]", payload),
        operator=operator,
        expect_data=False,
    )


def revoke_authorization(authorizations: Sequence[RevokeAuthorizationPayload], operator: str) -> None:
    operation = "revoke_authorization"
    payload = cast("list[RevokeAuthorizationPayload]", _batch(authorizations, operation))
    _validate_authorization_resources(payload, operation)
    _request(
        operation,
        http_delete,
        _system_path(AUTHORIZATIONS_PATH),
        cast("list[Any]", payload),
        operator=operator,
        expect_data=False,
    )


def list_authorization_subject(payload: AuthorizationSubjectQueryPayload) -> PaginationData:
    operation = "list_authorization_subject"
    page = payload.get("page", 1)
    page_size = payload.get("page_size", DEFAULT_PAGE_SIZE)
    _page_query(operation, page, page_size)
    data = _request(
        operation,
        http_post,
        _system_path(AUTHORIZATION_SUBJECTS_PATH),
        cast("dict[str, Any]", payload),
    )
    return _require_page(operation, data)
