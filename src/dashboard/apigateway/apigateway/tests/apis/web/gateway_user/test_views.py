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
from unittest import mock

import pytest

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "username, role",
    [
        ("admin", GatewayRoleEnum.ADMINISTRATOR.value),
        ("operator", GatewayRoleEnum.OPERATOR.value),
    ],
)
def test_retrieve_gateway_user_role(request_view, fake_gateway, username, role):
    GatewayMember.objects.update_or_create(
        gateway=fake_gateway,
        username=username,
        defaults={"role": role},
    )
    user = mock.MagicMock(
        username=username,
        is_authenticated=True,
        is_anonymous=False,
    )

    response = request_view(
        "GET",
        "gateway.user_role.retrieve",
        path_params={"gateway_id": fake_gateway.id},
        user=user,
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"role": role}


def test_retrieve_gateway_user_role_rejects_non_member(request_view, fake_gateway):
    user = mock.MagicMock(
        username="guest",
        is_authenticated=True,
        is_anonymous=False,
    )

    response = request_view(
        "GET",
        "gateway.user_role.retrieve",
        path_params={"gateway_id": fake_gateway.id},
        user=user,
    )

    assert response.status_code == 403


def test_retrieve_gateway_user_role_reuses_permission_queries(
    request_view,
    django_assert_num_queries,
    fake_gateway,
):
    with django_assert_num_queries(2):
        response = request_view(
            "GET",
            "gateway.user_role.retrieve",
            path_params={"gateway_id": fake_gateway.id},
        )

    assert response.status_code == 200
    assert "role" in response.json()["data"]
