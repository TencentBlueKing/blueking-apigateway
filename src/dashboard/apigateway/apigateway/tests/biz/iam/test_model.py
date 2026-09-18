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
from copy import deepcopy
from unittest.mock import call

import pytest

from apigateway.apps.rbac.constants import GATEWAY_ROLE_ACTIONS, GatewayActionEnum, GatewayResourceTypeEnum
from apigateway.biz.iam import GatewayIAMModelSyncer, GatewayIAMModelSyncResult
from apigateway.biz.iam.constants import BK_IAM_V4_SYSTEM_ID, SYSTEM_DESCRIPTION, SYSTEM_NAME
from apigateway.biz.iam.model import (
    get_gateway_iam_model,
)
from apigateway.components import bkiam


@pytest.fixture(autouse=True)
def _iam_settings(settings):
    settings.BK_APP_CODE = "bk-apigateway"
    settings.BK_IAM_V4_MANAGERS = ["admin", "maintainer"]


@pytest.fixture
def iam_client(mocker):
    client = mocker.patch("apigateway.biz.iam.model.bkiam")
    client.DEFAULT_PAGE_SIZE = bkiam.DEFAULT_PAGE_SIZE
    client.MAX_BATCH_SIZE = bkiam.MAX_BATCH_SIZE
    client.chunked = bkiam.chunked
    client.BkIamNotFoundError = bkiam.BkIamNotFoundError
    return client


def _desired_system():
    return {
        "id": BK_IAM_V4_SYSTEM_ID,
        "name": SYSTEM_NAME,
        "description": SYSTEM_DESCRIPTION,
        "managers": ["admin", "maintainer"],
        "clients": ["bk-apigateway"],
        "callback_url": "",
    }


def _page(items):
    return {"count": len(items), "results": items}


def _iam_model():
    return get_gateway_iam_model()


def test_gateway_iam_model_is_derived_from_local_rbac_declarations():
    model = get_gateway_iam_model()

    assert model == _iam_model()
    assert model["resource_types"] == [{"id": "gateway", "name": "网关", "ancestors": []}]
    assert [action["id"] for action in model["actions"]] == GatewayActionEnum.get_values()
    assert {action["resource_type_id"] for action in model["actions"]} == {GatewayResourceTypeEnum.GATEWAY.value}
    assert {
        role["id"]: tuple(action["id"] for action in role["actions"]) for role in model["roles"]
    } == GATEWAY_ROLE_ACTIONS


def _configure_existing_model(iam_client):
    iam_client.retrieve_system.return_value = _desired_system()
    model = _iam_model()
    iam_client.list_resource_type.return_value = _page(deepcopy(model["resource_types"]))
    iam_client.list_action.return_value = _page(deepcopy(model["actions"]))
    iam_client.list_role.return_value = _page(deepcopy(model["roles"]))


def _assert_no_writes(iam_client):
    for method_name in (
        "create_system",
        "update_system",
        "batch_create_resource_type",
        "update_resource_type",
        "batch_create_action",
        "update_action",
        "batch_create_role",
        "update_role",
        "batch_create_role_action",
        "batch_delete_role_action",
    ):
        getattr(iam_client, method_name).assert_not_called()


def test_sync_is_idempotent_when_model_matches(iam_client):
    _configure_existing_model(iam_client)

    result = GatewayIAMModelSyncer().sync()

    assert result == GatewayIAMModelSyncResult(unchanged=7)
    _assert_no_writes(iam_client)


def test_sync_creates_missing_model_in_dependency_order(iam_client):
    iam_client.retrieve_system.side_effect = bkiam.BkIamNotFoundError("missing")
    iam_client.list_resource_type.return_value = _page([])
    iam_client.list_action.return_value = _page([])
    iam_client.list_role.return_value = _page([])
    calls = []
    for method_name in (
        "create_system",
        "batch_create_resource_type",
        "batch_create_action",
        "batch_create_role",
    ):
        getattr(iam_client, method_name).side_effect = lambda *args, _name=method_name, **kwargs: calls.append(_name)

    result = GatewayIAMModelSyncer().sync()

    assert result == GatewayIAMModelSyncResult(created=7)
    assert calls == [
        "create_system",
        "batch_create_resource_type",
        "batch_create_action",
        "batch_create_role",
    ]
    iam_client.create_system.assert_called_once_with(_desired_system())


def test_sync_updates_mutable_fields_and_role_action_diff(iam_client):
    _configure_existing_model(iam_client)
    iam_client.retrieve_system.return_value["name"] = "旧系统"
    iam_client.list_resource_type.return_value["results"][0]["ancestors"] = ["legacy"]
    iam_client.list_action.return_value["results"][0]["name"] = "旧操作"
    administrator = iam_client.list_role.return_value["results"][0]
    administrator.update(
        {
            "name": "旧管理员",
            "description": "旧描述",
            "actions": [
                {"id": "operate_gateway", "resource_type_id": "gateway"},
                {"id": "unknown_action", "resource_type_id": "gateway"},
            ],
        }
    )

    result = GatewayIAMModelSyncer().sync()

    assert result == GatewayIAMModelSyncResult(
        updated=4,
        unchanged=3,
    )
    iam_client.update_system.assert_called_once_with({"name": "蓝鲸 API 网关"})
    iam_client.update_resource_type.assert_called_once_with("gateway", {"ancestors": []})
    iam_client.update_action.assert_called_once_with("manage_gateway", {"name": "管理网关"})
    iam_client.update_role.assert_called_once_with(
        "administrator",
        {
            "name": "管理员",
            "description": "蓝鲸 API 网关管理员角色",
        },
    )
    iam_client.batch_delete_role_action.assert_called_once_with("administrator", ["unknown_action"])
    iam_client.batch_create_role_action.assert_called_once_with(
        "administrator",
        [
            {"id": "approve_gateway_permission", "resource_type_id": "gateway"},
            {"id": "manage_gateway", "resource_type_id": "gateway"},
        ],
    )
    assert [item[0] for item in iam_client.mock_calls] == [
        "retrieve_system",
        "update_system",
        "list_resource_type",
        "update_resource_type",
        "list_action",
        "update_action",
        "list_role",
        "update_role",
        "batch_delete_role_action",
        "batch_create_role_action",
    ]


def test_sync_rejects_immutable_action_resource_type_drift(iam_client):
    _configure_existing_model(iam_client)
    iam_client.list_action.return_value["results"][0]["resource_type_id"] = "legacy"

    with pytest.raises(ValueError, match="immutable resource_type_id"):
        GatewayIAMModelSyncer().sync()


def test_sync_replaces_role_action_with_wrong_resource_type(iam_client):
    _configure_existing_model(iam_client)
    administrator = iam_client.list_role.return_value["results"][0]
    administrator["actions"][0]["resource_type_id"] = "legacy"

    result = GatewayIAMModelSyncer().sync()

    assert result == GatewayIAMModelSyncResult(unchanged=7)
    action_id = administrator["actions"][0]["id"]
    iam_client.batch_delete_role_action.assert_called_once_with("administrator", [action_id])
    iam_client.batch_create_role_action.assert_called_once_with(
        "administrator",
        [{"id": action_id, "resource_type_id": "gateway"}],
    )


def test_sync_lists_every_page_and_preserves_unknown_objects(iam_client):
    iam_client.retrieve_system.return_value = _desired_system()
    unknown_resource_types = [{"id": f"unknown-{index}", "name": "未知"} for index in range(100)]
    model = _iam_model()
    iam_client.list_resource_type.side_effect = [
        {"count": 101, "results": unknown_resource_types},
        {"count": 101, "results": deepcopy(model["resource_types"])},
    ]
    iam_client.list_action.return_value = _page(deepcopy(model["actions"]))
    iam_client.list_role.return_value = _page(deepcopy(model["roles"]))

    result = GatewayIAMModelSyncer().sync()

    assert result == GatewayIAMModelSyncResult(unchanged=7)
    assert iam_client.list_resource_type.call_args_list == [
        call(page=1, page_size=100),
        call(page=2, page_size=100),
    ]
    _assert_no_writes(iam_client)
