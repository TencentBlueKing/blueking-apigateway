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
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class AIBackendProviderConfig:
    endpoint: str
    model_endpoint: str
    openai_compatible: bool = True


AI_BACKEND_PROVIDER_REGISTRY: Mapping[str, AIBackendProviderConfig] = MappingProxyType(
    {
        "openai": AIBackendProviderConfig(
            endpoint="https://api.openai.com/v1/chat/completions",
            model_endpoint="https://api.openai.com/v1/models",
        ),
        "deepseek": AIBackendProviderConfig(
            endpoint="https://api.deepseek.com/chat/completions",
            model_endpoint="https://api.deepseek.com/models",
        ),
    }
)


def get_ai_backend_provider_config(provider: str) -> AIBackendProviderConfig | None:
    return AI_BACKEND_PROVIDER_REGISTRY.get(provider)
