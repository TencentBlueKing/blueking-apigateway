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
    ("name", "kind"),
    [
        ("bkai-demo", GatewayKindEnum.AI.value),
        ("bkaidev", GatewayKindEnum.AI.value),
        ("bkaidev-demo", GatewayKindEnum.AI.value),
        ("demo", GatewayKindEnum.NORMAL.value),
        ("bkaidev", GatewayKindEnum.NORMAL.value),
    ],
)
def test_validate_gateway_name_kind_accepts_valid_names(name, kind):
    validate_gateway_name_kind(name, kind)


@pytest.mark.parametrize(
    ("name", "kind", "expected_error"),
    [
        (
            "demo",
            GatewayKindEnum.AI.value,
            "AI 网关名称必须以【bkai-】开头。",
        ),
        (
            "bkaidevx",
            GatewayKindEnum.AI.value,
            "AI 网关名称必须以【bkai-】开头。",
        ),
        (
            "bkaidevfoo",
            GatewayKindEnum.AI.value,
            "AI 网关名称必须以【bkai-】开头。",
        ),
        (
            "bkai-demo",
            GatewayKindEnum.NORMAL.value,
            "前缀【bkai-】仅供 AI 网关使用。",
        ),
        (
            "bkai-demo",
            GatewayKindEnum.PROGRAMMABLE.value,
            "前缀【bkai-】仅供 AI 网关使用。",
        ),
    ],
)
def test_validate_gateway_name_kind_rejects_invalid_names(name, kind, expected_error):
    with pytest.raises(ValidationError) as exc_info:
        validate_gateway_name_kind(name, kind)

    assert str(exc_info.value.detail["name"]) == expected_error
