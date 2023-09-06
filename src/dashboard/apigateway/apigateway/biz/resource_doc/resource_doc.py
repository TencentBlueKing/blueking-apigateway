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
from collections import defaultdict
from typing import Dict, List

from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.common.audit.shortcuts import record_audit_log

from .constants import EN_RESOURCE_DOC_TMPL, ZH_RESOURCE_DOC_TMPL


class ResourceDocHandler:
    @staticmethod
    def record_audit_log_success(
        username: str,
        gateway_id: int,
        op_type: OpTypeEnum,
        instance_id: int,
        instance_name: str,
    ):
        comment = {
            OpTypeEnum.CREATE: _("创建资源文档"),
            OpTypeEnum.MODIFY: _("更新资源文档"),
            OpTypeEnum.DELETE: _("删除资源文档"),
        }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.RESOURCE_DOC.value,
            op_object_id=instance_id,
            op_object=instance_name,
            comment=comment,
        )

    @staticmethod
    def get_docs(resource_ids: List[int]) -> Dict[int, List]:
        if not resource_ids:
            return {}

        queryset = ResourceDoc.objects.filter(resource_id__in=resource_ids).values("id", "resource_id", "language")

        docs = defaultdict(list)
        for doc in queryset:
            docs[doc["resource_id"]].append(
                {
                    "id": doc["id"],
                    "language": doc["language"],
                }
            )

        return docs

    @staticmethod
    def get_docs_by_language(resource_ids: List[int], language: str) -> Dict[int, Dict]:
        if not (resource_ids and language):
            return {}

        queryset = ResourceDoc.objects.filter(resource_id__in=resource_ids, language=language).values(
            "id", "resource_id", "language"
        )
        return {doc["resource_id"]: {"id": doc["id"], "language": doc["language"]} for doc in queryset}

    @staticmethod
    def get_resource_doc_tmpl(gateway_name: str, language: str) -> str:
        """获取资源文档模板"""
        # 将模板中的网关名替换为当前网关名（作为包名，将中折线替换为下划线）
        if language == DocLanguageEnum.ZH.value:
            template = ZH_RESOURCE_DOC_TMPL

        elif language == DocLanguageEnum.EN.value:
            template = EN_RESOURCE_DOC_TMPL

        else:
            template = ""

        return template.replace("__GATEWAY_NAME__", gateway_name.replace("-", "_"))
