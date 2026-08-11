#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#

import pytest
from rest_framework.exceptions import ValidationError

from apigateway.core.constants import GatewayKindEnum
from apigateway.service.gateway_name import validate_gateway_name_kind


@pytest.mark.parametrize(
    ("name", "kind", "allow_bkaidev_ai_name"),
    [
        ("bkai-demo", GatewayKindEnum.AI.value, False),
        ("bkaidev", GatewayKindEnum.AI.value, True),
        ("bkaidev-demo", GatewayKindEnum.AI.value, True),
        ("demo", GatewayKindEnum.NORMAL.value, False),
        ("bkaidev", GatewayKindEnum.NORMAL.value, False),
    ],
)
def test_validate_gateway_name_kind_accepts_valid_names(name, kind, allow_bkaidev_ai_name):
    validate_gateway_name_kind(name, kind, allow_bkaidev_ai_name=allow_bkaidev_ai_name)


@pytest.mark.parametrize(
    ("name", "kind", "allow_bkaidev_ai_name", "expected_error"),
    [
        (
            "demo",
            GatewayKindEnum.AI.value,
            False,
            "AI 网关名称必须以【bkai-】开头。",
        ),
        (
            "bkaidev",
            GatewayKindEnum.AI.value,
            False,
            "AI 网关名称必须以【bkai-】开头。",
        ),
        (
            "demo",
            GatewayKindEnum.AI.value,
            True,
            "AI 网关名称必须以【bkai-】开头；自动化同步创建还允许【bkaidev】或【bkaidev-*】。",
        ),
        (
            "bkaidevx",
            GatewayKindEnum.AI.value,
            True,
            "AI 网关名称必须以【bkai-】开头；自动化同步创建还允许【bkaidev】或【bkaidev-*】。",
        ),
        (
            "bkaidevfoo",
            GatewayKindEnum.AI.value,
            True,
            "AI 网关名称必须以【bkai-】开头；自动化同步创建还允许【bkaidev】或【bkaidev-*】。",
        ),
        (
            "bkai-demo",
            GatewayKindEnum.NORMAL.value,
            False,
            "前缀【bkai-】仅供 AI 网关使用。",
        ),
        (
            "bkai-demo",
            GatewayKindEnum.PROGRAMMABLE.value,
            False,
            "前缀【bkai-】仅供 AI 网关使用。",
        ),
    ],
)
def test_validate_gateway_name_kind_rejects_invalid_names(name, kind, allow_bkaidev_ai_name, expected_error):
    with pytest.raises(ValidationError) as exc_info:
        validate_gateway_name_kind(name, kind, allow_bkaidev_ai_name=allow_bkaidev_ai_name)

    assert str(exc_info.value.detail["name"]) == expected_error
