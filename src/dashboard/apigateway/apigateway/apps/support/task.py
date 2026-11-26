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

import logging
from typing import List

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.ai import AIContentTypeEnum, AIHandler

logger = logging.getLogger(__name__)


def _get_docs_to_translate(doc_ids: List[int], gateway_id: int | None) -> List[ResourceDoc]:
    # 旧批量消息无法恢复请求网关，不能从文档归属推断调用者的授权范围。
    if gateway_id is None:
        raise ValueError("批量翻译任务缺少网关ID，请重新提交")

    docs = list(ResourceDoc.objects.filter(gateway_id=gateway_id, id__in=doc_ids))
    if not docs:
        raise ValueError("未找到需要翻译的文档")

    # 校验整个批次后再调用 AI，避免外部或失效 ID 导致部分执行。
    if {doc.id for doc in docs} != set(doc_ids):
        raise ValueError("文档不存在或不属于当前网关")

    return docs


@shared_task
def batch_translate_docs(doc_ids: List[int], target_language: str = "", *, gateway_id: int | None = None):
    """
    批量翻译文档任务

    注意：建议使用 delay_on_commit() 调用此任务，确保在数据库事务提交后执行

    Args:
        doc_ids: 需要翻译的文档ID列表
        target_language: 目标语言，如果为空则自动检测并翻译为相反语言
        gateway_id: 请求网关ID；旧消息缺少该值时安全终止，需从网关重新提交
    """
    logger.info("开始批量翻译任务，文档ID列表: %s", doc_ids)

    try:
        docs = _get_docs_to_translate(doc_ids, gateway_id)

        success_count = 0
        error_count = 0
        error_messages = []

        for doc in docs:
            if target_language and doc.language == target_language:
                logger.info("文档 %s 的目标语言 %s 已经是当前语言，跳过翻译", doc.id, target_language)
                continue

            trans_target_language = ""
            if doc.language == DocLanguageEnum.ZH.value:
                trans_target_language = DocLanguageEnum.EN.value
            elif doc.language == DocLanguageEnum.EN.value:
                trans_target_language = DocLanguageEnum.ZH.value
            try:
                # 检查是否已经存在目标语言的文档
                existing_doc = ResourceDoc.objects.filter(
                    gateway_id=gateway_id, resource_id=doc.resource_id, language=trans_target_language
                ).first()

                if existing_doc and (existing_doc.content or "").strip():
                    logger.info("文档 %s 的目标语言 %s 已存在，跳过翻译", doc.id, trans_target_language)
                    continue

                # 检查源文档是否有内容
                if not doc.content or not doc.content.strip():
                    logger.warning("文档 %s 内容为空，跳过翻译", doc.id)
                    continue

                # 调用AI翻译
                logger.info("开始翻译文档 %s，从 %s 到 %s", doc.id, doc.language, trans_target_language)

                response = AIHandler.analyze_content(
                    content_type=AIContentTypeEnum.DOC_TRANSLATE, content=doc.content, language=trans_target_language
                )

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
                            gateway_id=gateway_id,
                            resource_id=doc.resource_id,
                            type=doc.type,
                            language=trans_target_language,
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
def translate_single_doc(doc_id: int, target_language: str = ""):
    """
    翻译单个文档任务

    注意：建议使用 delay_on_commit() 调用此任务，确保在数据库事务提交后执行

    Args:
        doc_id: 需要翻译的文档ID
        target_language: 目标语言，如果为空则自动检测并翻译为相反语言
    """
    gateway_id = ResourceDoc.objects.filter(id=doc_id).values_list("gateway_id", flat=True).first()
    if gateway_id is None:
        return {"success": False, "message": "未找到需要翻译的文档"}
    return batch_translate_docs([doc_id], target_language, gateway_id=gateway_id)
