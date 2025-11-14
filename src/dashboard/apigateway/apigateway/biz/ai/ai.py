#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from django.conf import settings

from apigateway.components.ai import get_ai_client

from .constant import AIContentTypeEnum
from .prompt import PromptBuilder


class AIHandler:
    @staticmethod
    def analyze_content(content_type: AIContentTypeEnum, content: str, language: str, stream_enabled=False):
        """分析内容"""
        client = get_ai_client()
        return client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[{"role": "user", "content": PromptBuilder(content_type).build(content, language)}],
            stream=stream_enabled,
        )
