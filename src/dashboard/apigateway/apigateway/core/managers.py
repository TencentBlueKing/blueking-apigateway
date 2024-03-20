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
import itertools
import json
import operator
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

from cachetools import TTLCache, cached
from django.conf import settings
from django.db import models
from django.db.models import Q

from apigateway.common.constants import CACHE_MAXSIZE, CACHE_TIME_24_HOURS
from apigateway.core.constants import (
    DEFAULT_STAGE_NAME,
    StageStatusEnum,
)
from apigateway.utils.time import now_datetime

# - managers.py 下面不能存在跨 models 的操作，每个 manager 只关心自己的逻辑 (避免循环引用)


class StageManager(models.Manager):
    def get_names(self, gateway_id):
        return list(self.filter(gateway_id=gateway_id).values_list("name", flat=True))

    def get_ids(self, gateway_id):
        return list(self.filter(gateway_id=gateway_id).values_list("id", flat=True))

    def get_name_id_map(self, gateway):
        return dict(self.filter(gateway_id=gateway.id).values_list("name", "id"))

    def get_micro_gateway_id_to_fields(self, gateway_id: int) -> Dict[str, Dict[str, Any]]:
        return {
            item["micro_gateway_id"]: item
            for item in self.filter(gateway_id=gateway_id).values("id", "name", "micro_gateway_id")
            if item["micro_gateway_id"]
        }

    def get_gateway_name_to_active_stage_names(self, gateways) -> Dict[str, List[str]]:
        gateway_id_to_name = {g.id: g.name for g in gateways}

        gateway_name_to_stage_names = defaultdict(list)
        stages = self.filter(gateway_id__in=gateway_id_to_name.keys(), status=StageStatusEnum.ACTIVE.value).values(
            "gateway_id", "name"
        )
        for stage in stages:
            gateway_id = stage["gateway_id"]
            gateway_name = gateway_id_to_name[gateway_id]
            gateway_name_to_stage_names[gateway_name].append(stage["name"])

        return gateway_name_to_stage_names

    def get_name(self, gateway_id: int, id_: int) -> Optional[str]:
        return self.filter(gateway_id=gateway_id, id=id_).values_list("name", flat=True).first()


class ResourceVersionManager(models.Manager):
    def get_latest_version(self, gateway_id: int):
        """
        网关最新的版本
        """
        return self.filter(gateway_id=gateway_id).last()

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TIME_24_HOURS))
    def get_resources(self, gateway_id: int, id: int) -> Dict[int, dict]:
        resource_version = self.filter(gateway_id=gateway_id, id=id).first()
        if not resource_version:
            return {}

        resources = {}
        for resource in resource_version.data:
            resource_auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
            resources[resource["id"]] = {
                "id": resource["id"],
                "name": resource["name"],
                "description": resource.get("description") or "",
                "description_en": resource.get("description_en", ""),
                "method": resource["method"],
                "path": resource["path"],
                "match_subpath": resource.get("match_subpath", False),
                "is_public": resource["is_public"],
                "disabled_stages": resource.get("disabled_stages") or [],
                "allow_apply_permission": resource.get("allow_apply_permission", True),
                "resource_perm_required": resource_auth_config["resource_perm_required"],
                "app_verified_required": resource_auth_config["app_verified_required"],
                "user_verified_required": resource_auth_config["auth_verified_required"],
            }
        return resources

    def get_id_to_fields_map(
        self,
        gateway_id: Optional[int] = None,
        resource_version_ids: Optional[List[int]] = None,
    ) -> Dict[int, dict]:
        """获取资源版本信息"""
        queryset = self.all()

        if gateway_id is not None:
            queryset = queryset.filter(gateway_id=gateway_id)

        if resource_version_ids is not None:
            queryset = queryset.filter(id__in=resource_version_ids)

        return {rv["id"]: dict(rv) for rv in queryset.values("id", "name", "title", "version")}

    def get_id_by_name(self, gateway, name: str) -> Optional[int]:
        # 版本中 data 数据量较大，查询时不查询 data 数据
        ids = self.filter(gateway=gateway, name=name).values_list("id", flat=True)
        if not ids:
            return None
        return ids[0]

    def get_id_by_version(self, gateway_id: int, version: str) -> Optional[int]:
        if not version:
            return None

        ids = self.filter(gateway_id=gateway_id, version=version).values_list("id", flat=True)
        if not ids:
            return None
        return ids[0]

    def get_object_fields(self, id_: int) -> Dict[str, Any]:
        """获取字段数据，因部分字段数据量过大，因此只获取部分数据量不大的字段"""
        return self.filter(id=id_).values("id", "name", "title", "version").first() or {}

    def check_version_exists(self, gateway_id: int, version: str) -> bool:
        return self.filter(gateway_id=gateway_id, version=version).exists()

    def filter_objects_fields(self, gateway_id: int, version: Optional[str]):
        qs = self.filter(gateway_id=gateway_id)

        if version:
            qs = qs.filter(version=version)

        return qs.values("id", "version", "title", "comment")


class ReleaseManager(models.Manager):
    def get_released_stages(self, gateway=None, resource_version_ids=None):
        # 查询版本信息，并按照版本 ID 排序
        # 只显示 Stage 未下线的发布信息
        queryset = self.filter(stage__status=StageStatusEnum.ACTIVE.value)

        if gateway is not None:
            queryset = self.filter(gateway_id=gateway.id)

        if resource_version_ids is not None:
            queryset = queryset.filter(resource_version_id__in=resource_version_ids)

        releases = queryset.values("stage_id", "stage__name", "resource_version_id").order_by("resource_version_id")

        # 根据版本 ID 对列表中的数据进行分组，分组前，需要根据分组的 key 进行排序
        release_groups = itertools.groupby(releases, key=operator.itemgetter("resource_version_id"))

        # 获取每个版本对应的环境信息
        released_stages = {}
        for resource_version_id, group in release_groups:
            released_stages[resource_version_id] = sorted(
                [
                    {
                        "id": stage["stage_id"],
                        "name": stage["stage__name"],
                    }
                    for stage in group
                ],
                key=lambda x: x["name"],
            )

        return released_stages

    def get_resource_version_released_stage_names(self, resource_version_ids: List[int]) -> Dict[int, List[str]]:
        released_stages = self.get_released_stages(resource_version_ids=resource_version_ids)
        return {
            resource_version_id: [stage["name"] for stage in stages]
            for resource_version_id, stages in released_stages.items()
        }

    def save_release(self, gateway, stage, resource_version, comment, username):
        obj, created = self.get_or_create(
            gateway=gateway,
            stage=stage,
            defaults={
                "resource_version": resource_version,
                "comment": comment,
                "created_by": username,
                "updated_by": username,
                "created_time": now_datetime(),
                "updated_time": now_datetime(),
            },
        )
        if not created:
            obj.resource_version = resource_version
            obj.comment = comment
            obj.updated_by = username
            obj.updated_time = now_datetime()
            obj.save()

        return obj

    def delete_by_gateway_id(self, gateway_id):
        self.filter(gateway_id=gateway_id).delete()

    def delete_by_stage_ids(self, stage_ids):
        self.filter(stage_id__in=stage_ids).delete()

    def get_released_resource_version_ids(self, gateway_id: int, stage_name: Optional[str] = None) -> List[int]:
        qs = self.filter(gateway_id=gateway_id)

        if stage_name:
            qs = qs.filter(stage__name=stage_name)

        return list(qs.values_list("resource_version_id", flat=True))

    def get_released_resource_version_id(self, gateway_id: int, stage_name: str) -> Optional[int]:
        ids = self.get_released_resource_version_ids(gateway_id, stage_name)
        if not ids:
            return None
        return ids[0]


class ReleasedResourceManager(models.Manager):
    def save_released_resource(self, resource_version, force: bool = False) -> None:
        """保存资源版本中的资源配置"""
        queryset = self.filter(resource_version_id=resource_version.id)
        exists = queryset.exists()

        if exists and not force:
            return

        if exists:
            queryset.delete()

        resource_to_add = [
            self.model(
                gateway_id=resource_version.gateway_id,
                resource_version_id=resource_version.id,
                resource_id=resource["id"],
                resource_name=resource["name"],
                resource_method=resource["method"],
                resource_path=resource["path"],
                data=resource,
            )
            for resource in resource_version.data
        ]
        self.bulk_create(resource_to_add, batch_size=settings.RELEASED_RESOURCE_CREATE_BATCH_SIZE)

    def get_released_resource(self, gateway_id: int, resource_version_id: int, resource_name: str) -> Optional[dict]:
        released_resource = self.filter(
            gateway_id=gateway_id,
            resource_version_id=resource_version_id,
            resource_name=resource_name,
        ).first()
        if not released_resource:
            return None

        return self._parse_released_resource(released_resource)

    def filter_latest_released_resources(self, resource_ids: List[int]) -> List[dict]:
        """获取已发布资源的最新配置"""
        resources = (
            self.filter(resource_id__in=resource_ids)
            .order_by("resource_id", "-resource_version_id")
            .values("id", "resource_id", "resource_version_id")
        )

        ids = [next(group)["id"] for _, group in itertools.groupby(resources, key=operator.itemgetter("resource_id"))]

        return [self._parse_released_resource(resource) for resource in self.filter(id__in=ids)]

    def filter_resource_version_ids(self, resource_ids: List[int]) -> List[int]:
        """过滤出资源所属的资源版本号"""
        return list(
            self.filter(resource_id__in=resource_ids)
            .order_by("resource_version_id")
            .distinct()
            .values_list("resource_version_id", flat=True)
        )

    def get_recommended_stage_name(self, stage_names: List[str], disabled_stages: List[str]) -> Optional[str]:
        available_stages = set(stage_names) - set(disabled_stages)
        if not available_stages:
            return None

        if DEFAULT_STAGE_NAME in available_stages:
            return DEFAULT_STAGE_NAME

        return sorted(available_stages)[0]

    def _parse_released_resource(self, released_resource):
        resource = released_resource.data
        resource_auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
        return {
            "id": resource["id"],
            "name": resource["name"],
            "description": resource.get("description") or "",
            "description_en": resource.get("description_en", ""),
            "method": resource["method"],
            "path": resource["path"],
            "match_subpath": resource.get("match_subpath", False),
            "is_public": resource["is_public"],
            "disabled_stages": resource.get("disabled_stages") or [],
            "allow_apply_permission": resource.get("allow_apply_permission", True),
            "app_verified_required": resource_auth_config["app_verified_required"],
            "resource_perm_required": resource_auth_config["resource_perm_required"],
            "user_verified_required": resource_auth_config["auth_verified_required"],
        }


class ReleaseHistoryManager(models.Manager):
    # FIXME: not common, move to views.py
    def filter_release_history(
        self,
        gateway,
        query="",
        stage_id=None,
        created_by="",
        time_start=None,
        time_end=None,
        order_by=None,
        fuzzy=False,
    ):
        queryset = self.filter(gateway=gateway)

        # query 不是模型字段，仅支持模糊匹配，如需精确匹配，可使用具体字段
        if query and fuzzy:
            queryset = queryset.filter(
                Q(stage__name__contains=query)
                | Q(resource_version__name__contains=query)
                | Q(resource_version__title__contains=query)
                | Q(resource_version__version__contains=query)
            )

        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)

        if created_by:
            if fuzzy:
                queryset = queryset.filter(created_by__contains=created_by)
            else:
                queryset = queryset.filter(created_by=created_by)

        if time_start and time_end:
            # time_start、time_end 须同时存在，否则无效
            queryset = queryset.filter(created_time__range=(time_start, time_end))

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset.distinct()


class PublishEventManager(models.Manager):
    pass


class ContextManager(models.Manager):
    def get_config(self, scope_type, scope_id, type):
        return self.get(scope_type=scope_type, scope_id=scope_id, type=type).config

    def delete_by_scope_ids(self, scope_type, scope_ids):
        self.filter(scope_type=scope_type, scope_id__in=scope_ids).delete()


class MicroGatewayManager(models.Manager):
    def get_id_to_fields(self, ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        if not ids:
            return {}

        return {item["id"]: item for item in self.filter(id__in=ids).values("id", "name")}

    def get_default_shared_gateway(self):
        return self.get(is_shared=True, id=settings.DEFAULT_MICRO_GATEWAY_ID)
