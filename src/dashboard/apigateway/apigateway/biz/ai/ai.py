#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from openai import OpenAI

from apigateway.components.utils import gen_gateway_headers

from .constant import AIContentTypeEnum
from .prompt import ai_content_prompt_builders


class AIHandler:
    @staticmethod
    def get_ai_client():
        """获取 AI 客户端"""
        return OpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_OPEN_API_BASE_URL,
            default_headers=gen_gateway_headers(),
        )

    @staticmethod
    def analyze_content(content_type: AIContentTypeEnum, content: str, stream_enabled=False):
        """分析内容"""
        client = AIHandler().get_ai_client()
        return client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[{"role": "user", "content": ai_content_prompt_builders[content_type](content)}],
            stream=stream_enabled,
        )
