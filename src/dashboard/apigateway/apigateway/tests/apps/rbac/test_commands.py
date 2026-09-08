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
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from django_dynamic_fixture import G

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


def test_check_gateway_rbac_data_succeeds(fake_gateway):
    GatewayMember.objects.filter(gateway=fake_gateway).update(expires=timezone.now() - timedelta(days=1))

    call_command("check_gateway_rbac_data")


def test_check_gateway_rbac_data_rejects_empty_gateway():
    G(Gateway)

    with pytest.raises(CommandError):
        call_command("check_gateway_rbac_data")


def test_check_gateway_rbac_data_rejects_gateway_without_administrator():
    gateway = G(Gateway)
    G(
        GatewayMember,
        gateway=gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    with pytest.raises(CommandError):
        call_command("check_gateway_rbac_data")


@pytest.mark.parametrize(
    "username, role",
    [
        ("member", "invalid"),
        ("", GatewayRoleEnum.ADMINISTRATOR.value),
        (" ", GatewayRoleEnum.ADMINISTRATOR.value),
        (" member ", GatewayRoleEnum.ADMINISTRATOR.value),
    ],
)
def test_check_gateway_rbac_data_rejects_invalid_member(fake_gateway, username, role):
    GatewayMember.objects.create(
        gateway=fake_gateway,
        username=username,
        role=role,
    )

    with pytest.raises(CommandError):
        call_command("check_gateway_rbac_data")
