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

from apigateway.core.constants import ResourceKindEnum
from apigateway.service.plugin import (
    get_incompatible_plugin_type_codes,
    is_plugin_allowed_for_kind,
)


@pytest.mark.parametrize(
    ("plugin_type_code", "kind", "expected"),
    [
        ("bk-cors", ResourceKindEnum.STANDARD.value, True),
        ("bk-cors", ResourceKindEnum.AI.value, True),
        ("ai-rate-limiting", ResourceKindEnum.AI.value, True),
        ("ai-rate-limiting", ResourceKindEnum.STANDARD.value, False),
        ("bk-header-rewrite", ResourceKindEnum.STANDARD.value, True),
        ("bk-header-rewrite", ResourceKindEnum.AI.value, False),
        ("ai-proxy", ResourceKindEnum.STANDARD.value, False),
        ("ai-proxy", ResourceKindEnum.AI.value, False),
        ("ai-proxy-multi", ResourceKindEnum.AI.value, False),
        ("unknown-plugin", ResourceKindEnum.STANDARD.value, True),
        ("unknown-plugin", ResourceKindEnum.AI.value, False),
    ],
)
def test_is_plugin_allowed_for_kind(plugin_type_code, kind, expected):
    assert is_plugin_allowed_for_kind(plugin_type_code, kind) is expected


def test_get_incompatible_plugin_type_codes_preserves_input_order():
    assert get_incompatible_plugin_type_codes(
        ["bk-cors", "bk-header-rewrite", "ai-proxy", "unknown-plugin"],
        ResourceKindEnum.AI.value,
    ) == ["bk-header-rewrite", "ai-proxy", "unknown-plugin"]


def test_is_plugin_allowed_for_kind_rejects_unknown_kind():
    with pytest.raises(ValueError, match="unsupported kind"):
        is_plugin_allowed_for_kind("bk-cors", "unknown")
