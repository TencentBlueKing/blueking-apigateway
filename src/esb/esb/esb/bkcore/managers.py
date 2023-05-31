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
from typing import Dict, List, Optional

from django.db import models

from esb.bkcore.constants import DataTypeEnum


class SystemManager(models.Manager):
    def get_name_to_obj_map(self):
        return {system.name: system for system in self.all()}

    def get_system_id_to_timeout(self) -> Dict[int, Optional[int]]:
        return dict(self.values_list("id", "timeout"))

    def get_official_ids(self) -> List[int]:
        return list(self.exclude(data_type=DataTypeEnum.CUSTOM.value).values_list("id", flat=True))


class ESBChannelManager(models.Manager):
    def get_best_matched_channel(self, method: str, paths: List[str]):
        """
        获取最匹配给定条件的 channel
        """
        qs = self.filter(path__in=paths)

        # 数据库中有匹配方法的 channel
        channel = qs.filter(method=method).first()
        if channel:
            return channel

        if method not in ["GET", "POST"]:
            return None

        # 默认支持 GET 和 POST 方法
        return qs.filter(method="").first()

    def get_field_values(self, id_: int) -> Optional[dict]:
        value = self.filter(id=id_).values("name", "system__name").first()
        if not value:
            return None

        return {
            "name": value["name"],
            "system_name": value["system__name"],
        }

    def filter_channels(self, system_ids=None, is_public=None, is_active=None):
        queryset = self.all()

        if system_ids is not None:
            queryset = queryset.filter(system_id__in=system_ids)

        if is_public is not None:
            queryset = queryset.filter(is_public=is_public)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        return queryset


class ESBChannelExtendManager(models.Manager):
    pass


class DocCategoryManager(models.Manager):
    def get_name_to_obj_map(self):
        return {category.name: category for category in self.all()}


class SystemDocCategoryManager(models.Manager):
    pass


class AppComponentPermissionManager(models.Manager):
    def has_permission(self, bk_app_code: str, component_id: int) -> bool:
        return self.filter(bk_app_code=bk_app_code, component_id=component_id).exists()


class AppPermissionApplyRecordManager(models.Manager):
    pass


class AppPermissionApplyStatusManager(models.Manager):
    pass
