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

import logging
from typing import List

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.ai.ai import AIHandler
from apigateway.biz.ai.constant import AIContentTypeEnum

logger = logging.getLogger(__name__)


@shared_task
def batch_translate_docs(doc_ids: List[int], target_language: str = DocLanguageEnum.EN.value):
    """
    批量翻译文档任务

    注意：建议使用 delay_on_commit() 调用此任务，确保在数据库事务提交后执行

    Args:
        doc_ids: 需要翻译的文档ID列表
        target_language: 目标语言，如果为None则自动检测并翻译为相反语言
    """
    logger.info("开始批量翻译任务，文档ID列表: %s", doc_ids)

    try:
        # 获取需要翻译的文档
        docs = ResourceDoc.objects.filter(id__in=doc_ids).select_related("gateway")

        if not docs.exists():
            logger.warning("未找到需要翻译的文档，ID列表: %s", doc_ids)
            return {"success": False, "message": "未找到需要翻译的文档"}

        success_count = 0
        error_count = 0
        error_messages = []

        for doc in docs:
            try:
                # 如果目标语言未指定，则根据当前语言自动选择相反语言
                if not target_language:
                    if doc.language == DocLanguageEnum.ZH.value:
                        target_language = DocLanguageEnum.EN.value
                    elif doc.language == DocLanguageEnum.EN.value:
                        target_language = DocLanguageEnum.ZH.value
                    else:
                        # 默认翻译为英文
                        target_language = DocLanguageEnum.EN.value

                # 检查是否已经存在目标语言的文档
                existing_doc = ResourceDoc.objects.filter(
                    gateway=doc.gateway, resource_id=doc.resource_id, language=target_language
                ).first()

                if existing_doc and existing_doc.content.strip():
                    logger.info("文档 %s 的目标语言 %s 已存在，跳过翻译", doc.id, target_language)
                    continue

                # 检查源文档是否有内容
                if not doc.content or not doc.content.strip():
                    logger.warning("文档 %s 内容为空，跳过翻译", doc.id)
                    continue

                # 调用AI翻译
                logger.info("开始翻译文档 %s，从 %s 到 %s", doc.id, doc.language, target_language)

                response = AIHandler.analyze_content(content_type=AIContentTypeEnum.DOC_TRANSLATE, content=doc.content)

                translated_content = response.choices[0].message.content

                # 保存翻译结果
                with transaction.atomic():
                    if existing_doc:
                        # 更新已存在的文档
                        existing_doc.content = translated_content
                        existing_doc.updated_time = timezone.now()
                        existing_doc.save(update_fields=["content", "updated_time"])
                        logger.info("更新文档 %s 的翻译内容", existing_doc.id)
                    else:
                        # 创建新的翻译文档
                        new_doc = ResourceDoc.objects.create(
                            gateway=doc.gateway,
                            resource_id=doc.resource_id,
                            type=doc.type,
                            language=target_language,
                            source=doc.source,
                            content=translated_content,
                            created_by=doc.created_by,
                            updated_by=doc.updated_by,
                        )
                        logger.info("创建新翻译文档 %s", new_doc.id)

                success_count += 1
                logger.info("文档 %s 翻译完成", doc.id)

            except Exception as e:
                error_count += 1
                error_msg = f"翻译文档 {doc.id} 失败: {str(e)}"
                error_messages.append(error_msg)
                logger.exception("翻译文档 %s 失败", doc.id)

        result = {
            "success": True,
            "message": f"批量翻译完成，成功: {success_count}, 失败: {error_count}",
            "success_count": success_count,
            "error_count": error_count,
            "error_messages": error_messages,
        }

        logger.info("批量翻译任务完成: %s", result)
        return result

    except Exception as e:
        error_msg = f"批量翻译任务执行失败: {str(e)}"
        logger.exception("批量翻译任务执行失败")
        return {"success": False, "message": error_msg}


@shared_task
def translate_single_doc(doc_id: int, target_language: str = DocLanguageEnum.EN.value):
    """
    翻译单个文档任务

    注意：建议使用 delay_on_commit() 调用此任务，确保在数据库事务提交后执行

    Args:
        doc_id: 需要翻译的文档ID
        target_language: 目标语言，如果为None则自动检测并翻译为相反语言
    """
    return batch_translate_docs([doc_id], target_language)
