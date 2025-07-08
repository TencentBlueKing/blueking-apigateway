# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from typing import Dict, Optional

from django.db import models

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.core.constants import GatewayStatusEnum

RELEASED_RESOURCE_DOC_CREATE_BATCH_SIZE = 50


class ResourceDocVersionManager(models.Manager):
    def get_by_resource_version_id(self, gateway_id: int, resource_version_id: int):
        return self.filter(gateway_id=gateway_id, resource_version_id=resource_version_id).first()

    def get_latest_version(self, gateway_id: int):
        return self.filter(gateway_id=gateway_id).order_by("-id").first()


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
        # 异步同时 (多个 stage 同时发布同一版本) 更新会存在一些冲突问题
        self.bulk_create(
            resource_doc_to_add, batch_size=RELEASED_RESOURCE_DOC_CREATE_BATCH_SIZE, ignore_conflicts=True
        )

    def get_doc_updated_time(self, gateway_id: int, resource_version_id: int, resource_id: int) -> Dict[str, str]:
        qs = self.filter(gateway_id=gateway_id, resource_version_id=resource_version_id, resource_id=resource_id)
        return {doc.language: doc.data["updated_time"] for doc in qs}


class GatewaySDKManager(models.Manager):
    def get_latest_sdk(self, gateway_id: int, language: str):
        return self.filter(gateway_id=gateway_id, language=language).order_by("-id").first()

    def get_resource_version_language_sdk_count(self, resource_version_id: int, language: str):
        return self.filter(resource_version_id=resource_version_id, language=language).count()

    def should_be_set_to_public_latest(
        self, gateway_id: int, resource_version_id: int, is_uploaded_to_pypi: bool
    ) -> bool:
        """是否应该将此 SDK 设置为网关最新公开的 SDK"""
        if not is_uploaded_to_pypi:
            return False

        public_latest_sdk = self.filter(is_recommended=True, gateway_id=gateway_id).first()
        # 最新 SDK 的版本比当前版本更新，则当前 SDK 非最新 SDK
        if (
            public_latest_sdk
            and public_latest_sdk.resource_version_id
            and public_latest_sdk.resource_version_id > resource_version_id
        ):
            return False

        return True

    def filter_recommended_sdks(self, language: str, gateway_id: Optional[int] = None):
        """
        获取公开网关的最新公开 SDK
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
