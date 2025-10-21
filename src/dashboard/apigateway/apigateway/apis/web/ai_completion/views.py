# -*- coding: utf-8 -*-
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
import json
import logging

from blue_krill.async_utils.django_utils import delay_on_commit
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.docs.ai_batch_translate import batch_translate_docs
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.ai.ai import AIHandler
from apigateway.biz.ai.constant import AIContentTypeEnum
from apigateway.utils.responses import OKJsonResponse

from .serializers import AICompletionInputSLZ, BatchTranslateInputSLZ, BatchTranslateOutputSLZ

logger = logging.getLogger(__name__)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=AICompletionInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.AI_Completion"],
        operation_description="AI Completion",
    ),
)
class AICompletionCreateApi(generics.CreateAPIView):
    serializer_class = AICompletionInputSLZ

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取验证后的参数
        content_type = serializer.validated_data["inputs"]["type"]
        user_content = serializer.validated_data["inputs"]["input"]
        enable_streaming = serializer.validated_data["inputs"]["enable_streaming"]
        if enable_streaming:
            # 流式响应处理
            return self.handle_streaming_response(content_type, user_content)
        # 普通响应处理
        return self.handle_normal_response(content_type, user_content)

    def handle_streaming_response(self, content_type: AIContentTypeEnum, content: str):
        def generate_stream():
            try:
                stream = AIHandler.analyze_content(content_type, content, stream_enabled=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                yield "data: [DONE]\n\n"  # 结束标志

        return StreamingHttpResponse(
            generate_stream(), content_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    def handle_normal_response(self, content_type: AIContentTypeEnum, content: str):
        response = AIHandler.analyze_content(content_type, content)
        return OKJsonResponse(
            data={
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            }
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=BatchTranslateInputSLZ(),
        responses={status.HTTP_200_OK: BatchTranslateOutputSLZ()},
        tags=["WebAPI.AI_Completion"],
        operation_description="批量翻译文档",
    ),
)
class BatchTranslateApi(generics.CreateAPIView):
    """批量翻译文档API"""

    serializer_class = BatchTranslateInputSLZ

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_ids = serializer.validated_data["doc_ids"]
        target_language = serializer.validated_data.get("target_language")

        # 如果没有网关上下文，直接验证文档是否存在
        docs = ResourceDoc.objects.filter(id__in=doc_ids)
        if not docs.exists():
            return OKJsonResponse(data={"error": "未找到指定的文档"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # 启动异步翻译任务，使用delay_on_commit确保在事务提交后执行
            delay_on_commit(batch_translate_docs, doc_ids=doc_ids, target_language=target_language)

            logger.info("启动批量翻译任务，文档ID列表: %s", doc_ids)

            return OKJsonResponse(data={"message": "批量翻译任务已启动", "doc_count": len(doc_ids)})

        except Exception as e:
            logger.exception("启动批量翻译任务失败")
            return OKJsonResponse(
                data={"error": f"启动批量翻译任务失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
