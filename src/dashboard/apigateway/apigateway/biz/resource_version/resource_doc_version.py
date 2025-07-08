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
from collections import defaultdict
from typing import Any, Dict, List, Optional

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ReleasedResourceDoc, ResourceDoc, ResourceDocVersion
from apigateway.biz.resource_doc import ResourceDocHandler
from apigateway.core.models import Release


class ResourceDocVersionHandler:
    @staticmethod
    def make_version(gateway_id: int):
        docs = ResourceDoc.objects.filter(gateway_id=gateway_id).all()
        return [d.snapshot(as_dict=True) for d in docs]

    @staticmethod
    def get_doc_data_by_rv_or_new(gateway_id: int, resource_version_id: Optional[int]) -> List[Any]:
        """获取版本中文档内容"""
        if resource_version_id:
            try:
                return ResourceDocVersion.objects.get(
                    gateway_id=gateway_id, resource_version_id=resource_version_id
                ).data
            except ResourceDocVersion.DoesNotExist:
                return []

        return ResourceDocVersionHandler().make_version(gateway_id)

    @staticmethod
    def get_doc_updated_time(gateway_id: int, resource_version_id: Optional[int]):
        """获取文档更新时间

        @return:
        {
            1: {
                "zh": "1970-01-01 12:30:50 +8000",
                "en": "1970-01-01 12:30:50 +8000"
            }
        }
        """
        doc_data = ResourceDocVersionHandler.get_doc_data_by_rv_or_new(gateway_id, resource_version_id)

        result: Dict[int, Dict[str, Any]] = defaultdict(dict)
        for doc in doc_data:
            language = doc.get("language", DocLanguageEnum.ZH.value)
            result[doc["resource_id"]][language] = doc["updated_time"]

        return result

    @staticmethod
    def need_new_version(gateway_id: int) -> bool:
        """是否需要创建新的资源文档版本"""
        latest_version = ResourceDocVersion.objects.get_latest_version(gateway_id)
        doc_last_updated_time = ResourceDocHandler.get_last_updated_time(gateway_id)

        if not (latest_version or doc_last_updated_time):
            return False

        if not latest_version:
            return True

        if doc_last_updated_time and doc_last_updated_time > latest_version.created_time:
            return True

        # 文档不可直接删除，资源删除导致的文档删除，在判断"是否需要创建资源版本"时校验
        return False

    @staticmethod
    def clear_unreleased_resource_doc(gateway_id: int) -> None:
        """清理未发布的资源文档，如已发布版本被新版本替代的情况"""
        resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
        ReleasedResourceDoc.objects.filter(gateway_id=gateway_id).exclude(
            resource_version_id__in=resource_version_ids
        ).delete()
