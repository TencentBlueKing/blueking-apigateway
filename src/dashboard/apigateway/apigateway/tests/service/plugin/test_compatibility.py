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
from apigateway.service.plugin import AI_ONLY_PLUGIN_CODES, is_plugin_compatible_with_resource_kind


def test_ai_only_plugin_codes():
    assert {
        "ai-rate-limiting",
        "ai-prompt-guard",
        "ai-prompt-decorator",
    } == AI_ONLY_PLUGIN_CODES


@pytest.mark.parametrize(
    ("resource_kind", "plugin_type_code", "expected"),
    [
        (ResourceKindEnum.AI.value, "ai-rate-limiting", True),
        (ResourceKindEnum.AI.value, "ai-prompt-guard", True),
        (ResourceKindEnum.AI.value, "ai-prompt-decorator", True),
        (ResourceKindEnum.STANDARD.value, "ai-rate-limiting", False),
        (ResourceKindEnum.STANDARD.value, "ai-prompt-guard", False),
        (ResourceKindEnum.STANDARD.value, "ai-prompt-decorator", False),
        (None, "ai-rate-limiting", False),
        (ResourceKindEnum.AI.value, "bk-cors", True),
        (ResourceKindEnum.AI.value, "bk-header-rewrite", False),
        (ResourceKindEnum.AI.value, "bk-query-string-rewrite", False),
        (ResourceKindEnum.AI.value, "bk-status-rewrite", False),
        (ResourceKindEnum.AI.value, "bk-traffic-label", False),
        (ResourceKindEnum.AI.value, "api-breaker", False),
        (ResourceKindEnum.AI.value, "response-rewrite", False),
        (ResourceKindEnum.AI.value, "proxy-cache", False),
        (ResourceKindEnum.AI.value, "bk-legacy-invalid-params", False),
        (ResourceKindEnum.STANDARD.value, "bk-cors", True),
        (ResourceKindEnum.STANDARD.value, "bk-header-rewrite", True),
        (None, "bk-cors", True),
        (None, "bk-header-rewrite", True),
    ],
)
def test_is_plugin_compatible_with_resource_kind(resource_kind, plugin_type_code, expected):
    assert is_plugin_compatible_with_resource_kind(plugin_type_code, resource_kind) is expected
