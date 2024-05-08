# -*- coding: utf-8 -*-
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
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import models
from django.db.models import Q

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.core.constants import GatewayStatusEnum


class ResourceDocVersionManager(models.Manager):
    def make_version(self, gateway_id):
        from apigateway.apps.support.models import ResourceDoc

        docs = ResourceDoc.objects.filter(gateway_id=gateway_id).all()
        return [d.snapshot(as_dict=True) for d in docs]

    def get_by_resource_version_id(self, gateway_id: int, resource_version_id: int):
        return self.filter(gateway_id=gateway_id, resource_version_id=resource_version_id).first()

    def get_latest_version(self, gateway_id):
        return self.filter(gateway_id=gateway_id).order_by("-id").first()

    def get_doc_data_by_rv_or_new(self, gateway_id: int, resource_version_id: Optional[int]) -> List[Any]:
        """获取版本中文档内容"""
        if resource_version_id:
            try:
                return self.get(gateway_id=gateway_id, resource_version_id=resource_version_id).data
            except self.model.DoesNotExist:
                return []

        return self.make_version(gateway_id)

    def get_doc_updated_time(self, gateway_id: int, resource_version_id: Optional[int]):
        """获取文档更新时间

        @return:
        {
            1: {
                "zh": "1970-01-01 12:30:50 +8000",
                "en": "1970-01-01 12:30:50 +8000"
            }
        }
        """
        doc_data = self.get_doc_data_by_rv_or_new(gateway_id, resource_version_id)

        result: Dict[int, Dict[str, Any]] = defaultdict(dict)
        for doc in doc_data:
            language = doc.get("language", DocLanguageEnum.ZH.value)
            result[doc["resource_id"]][language] = doc["updated_time"]

        return result


class ReleasedResourceDocManager(models.Manager):
    def save_released_resource_doc(self, resource_doc_version, force: bool = False) -> None:
        """将文档版本中的文档，存储到已发布文档，方便文档查询"""
        if not resource_doc_version:
            return

        queryset = self.filter(resource_version_id=resource_doc_version.resource_version_id)
        exists = queryset.exists()

        if exists and not force:
            return

        if exists:
            queryset.delete()

        resource_doc_to_add = [
            self.model(
                gateway_id=resource_doc_version.gateway_id,
                resource_version_id=resource_doc_version.resource_version_id,
                resource_id=doc["resource_id"],
                language=doc.get("language", DocLanguageEnum.ZH.value),
                data=doc,
            )
            for doc in resource_doc_version.data
        ]
        self.bulk_create(resource_doc_to_add, batch_size=settings.RELEASED_RESOURCE_DOC_CREATE_BATCH_SIZE)

    def clear_unreleased_resource_doc(self, gateway_id: int) -> None:
        """清理未发布的资源文档，如已发布版本被新版本替代的情况"""
        from apigateway.core.models import Release

        resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
        self.filter(gateway_id=gateway_id).exclude(resource_version_id__in=resource_version_ids).delete()

    def get_doc_updated_time(self, gateway_id: int, resource_version_id: int, resource_id: int) -> Dict[str, str]:
        qs = self.filter(gateway_id=gateway_id, resource_version_id=resource_version_id, resource_id=resource_id)
        return {doc.language: doc.data["updated_time"] for doc in qs}


class APISDKManager(models.Manager):
    # FIXME: move to views.py
    def filter_sdk(
        self,
        gateway,
        language=None,
        order_by=None,
        version_number="",
        resource_version_id=None,
        fuzzy=False,
        keyword=None,
    ):
        queryset = self.filter(gateway=gateway)

        if keyword:
            queryset = queryset.filter(
                Q(language__icontains=keyword)
                | Q(version_number__contains=keyword)
                | Q(resource_version__version__contains=keyword)
            )

        if language:
            queryset = queryset.filter(language=language)

        if version_number:
            if fuzzy:
                queryset = queryset.filter(version_number__contains=version_number)
            else:
                queryset = queryset.filter(version_number=version_number)

        if resource_version_id is not None:
            queryset = queryset.filter(resource_version_id=resource_version_id)

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    def get_latest_sdk(self, gateway_id, language):
        return self.filter(gateway_id=gateway_id, language=language).order_by("-id").first()

    def get_resource_version_language_sdk_count(self, resource_version_id, language):
        return self.filter(resource_version_id=resource_version_id, language=language).count()

    def should_be_set_to_public_latest(
        self, gateway_id: int, resource_version_id: int, is_uploaded_to_pypi: bool
    ) -> bool:
        """是否应该将此SDK设置为网关最新公开的SDK"""
        if not is_uploaded_to_pypi:
            return False

        public_latest_sdk = self.filter(is_recommended=True, gateway_id=gateway_id).first()
        # 最新 SDK 的版本比当前版本更新，则当前SDK非最新SDK
        if (
            public_latest_sdk
            and public_latest_sdk.resource_version_id
            and public_latest_sdk.resource_version_id > resource_version_id
        ):
            return False

        return True

    def filter_recommended_sdks(self, language, gateway_id=None):
        """
        获取公开网关的最新公开SDK
        """
        queryset = self.filter(
            is_recommended=True,
            language=language,
            gateway__is_public=True,
            gateway__status=GatewayStatusEnum.ACTIVE.value,
        )
        if gateway_id is not None:
            queryset = queryset.filter(gateway_id=gateway_id)

        return queryset
