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
import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils.translation import gettext as _

from apigateway.apps.esb.bkcore.models import ComponentReleaseHistory
from apigateway.biz.releaser import ReleaseBatchHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import Gateway, ResourceVersion, Stage


@dataclass
class ComponentReleaser:
    gateway: Gateway
    username: str
    release_history: Optional[ComponentReleaseHistory] = None
    resource_version: Optional[ResourceVersion] = None
    access_token: str = ""

    def create_release_history(self):
        self.release_history = ComponentReleaseHistory.objects.create(
            resource_version_id=0,
            data=[],
            status=ReleaseStatusEnum.RELEASING.value,
            created_by=self.username,
        )

    @transaction.atomic
    def create_resource_version(self):
        assert self.release_history

        # resource_version_manager = ResourceVersionManager()
        version = self._prepare_version(self.gateway.id, self.release_history.id)
        # self.resource_version = resource_version_manager.create_resource_version(
        self.resource_version = ResourceVersionHandler.create_resource_version(
            self.gateway,
            data={
                "version": version,
                "title": version,
                "comment": _("同步组件到 API 网关"),
            },
            username=self.username,
        )

    @transaction.atomic
    def release(self):
        """发布组件对应的网关，并记录组件发布历史记录"""
        assert self.resource_version

        release_manager = ReleaseBatchHandler(access_token=self.access_token)
        release_manager.release_batch(
            self.gateway,
            {
                "stage_ids": Stage.objects.get_ids(self.gateway.id),
                "resource_version_id": self.resource_version.id,
                "comment": _("同步组件到 API 网关"),
            },
            self.username,
        )

    def record_updated_resources(self, updated_resources: List[Dict[str, Any]]):
        # 在 mark success or fail 时统一 save
        if not self.release_history:
            return
        self.release_history.data = updated_resources

    def mark_release_fail(self, message: str):
        if not self.release_history:
            return
        self.release_history.resource_version_id = self._get_resource_version_id()
        self.release_history.status = ReleaseStatusEnum.FAILURE.value
        self.release_history.message = message

        self.release_history.save()

    def mark_release_success(self):
        if not self.release_history:
            return
        self.release_history.resource_version_id = self._get_resource_version_id()
        self.release_history.status = ReleaseStatusEnum.SUCCESS.value
        self.release_history.message = "OK"

        self.release_history.save()

    def _prepare_version(self, gateway_id: int, history_id: int) -> str:
        """准备网关资源版本的版本号

        - 为防止因用户主动发布导致的版本号冲突，在版本号已存在时，加一个时间字符串
        """
        version = f"1.0.{history_id}"
        if ResourceVersion.objects.check_version_exists(gateway_id, version):
            return "{version}+{now}".format(version=version, now=datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

        return version

    def _get_resource_version_id(self):
        return self.resource_version and self.resource_version.id or 0
