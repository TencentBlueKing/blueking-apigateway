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
from typing import Any, Dict, Iterable, List, Optional, Union

from cachetools import TTLCache, cached
from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from apigateway.common.constants import CACHE_MAXSIZE, CacheTimeLevel
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import InstanceDeleteError
from apigateway.common.factories import SchemaFactory
from apigateway.common.mcryptography import AESCipherManager
from apigateway.core.constants import (
    DEFAULT_STAGE_NAME,
    STAGE_VAR_PATTERN,
    APIHostingTypeEnum,
    BackendConfigTypeEnum,
    GatewayStatusEnum,
    ProxyTypeEnum,
    SSLCertificateBindingScopeTypeEnum,
    StageStatusEnum,
)
from apigateway.utils.crypto import KeyGenerator
from apigateway.utils.time import now_datetime

# TODO
# - 所有带 FIXME 的都需要处理，挪到合适的层
# - managers.py 下面不能存在跨 models 的操作，每个 manager 只关心自己的逻辑 (避免循环引用)


class GatewayManager(models.Manager):
    def search_gateways(self, username, name=None, order_by=None):
        """
        根据用户、网关名筛选网关
        """
        queryset = self.filter(Q(created_by=username) | Q(_maintainers__contains=username))

        if name:
            queryset = queryset.filter(name__contains=name)

        if order_by:
            queryset = queryset.order_by(order_by)

        return [gateway for gateway in queryset if gateway.has_permission(username)]

    def fetch_authorized_gateway_ids(self, username: str) -> List[str]:
        """获取用户有权限的网关 ID 列表"""
        queryset = self.filter(_maintainers__contains=username)
        return [gateway.id for gateway in queryset if gateway.has_permission(username)]

    def get_or_new_gateway(self, name):
        if self.filter(name=name).exists():
            return self.get(name=name)
        gateway = self.model()
        gateway.name = name

        return gateway

    def filter_id_object_map(self, ids=None):
        """
        获取网关 ID 对
        """
        queryset = self.all()
        if ids is not None:
            queryset = queryset.filter(id__in=ids)
        return {gateway.id: gateway for gateway in queryset}

    def filter_micro_and_active_queryset(self):
        """获取托管类型为微网关，且已启用的网关，用于获取可发布到共享微网关实例的网关"""
        return self.filter(hosting_type=APIHostingTypeEnum.MICRO.value, status=GatewayStatusEnum.ACTIVE.value)

    def query_micro_and_active_ids(self, ids: Union[List[int], None] = None) -> List[int]:
        """获取托管类型为微网关，且已启用的网关 ID 列表；如果给定了网关 ID 列表，则返回其中符合条件的 ID 列表"""
        queryset = self.filter_micro_and_active_queryset()
        if ids is not None:
            queryset = queryset.filter(id__in=ids)

        return list(queryset.values_list("id", flat=True))


class StageManager(models.Manager):
    def get_names(self, gateway_id):
        return list(self.filter(gateway_id=gateway_id).values_list("name", flat=True))

    def get_ids(self, gateway_id):
        return list(self.filter(gateway_id=gateway_id).values_list("id", flat=True))

    def get_name_id_map(self, gateway):
        return dict(self.filter(gateway_id=gateway.id).values_list("name", "id"))

    def get_id_to_fields(self, gateway_id: int, fields: List[str]) -> Dict[int, Dict[str, Any]]:
        return {stage["id"]: stage for stage in self.filter(gateway_id=gateway_id).values(*fields)}

    def filter_valid_ids(self, gateway, ids):
        return list(self.filter(gateway_id=gateway.id, id__in=ids).values_list("id", flat=True))

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


class ResourceManager(models.Manager):
    def filter_by_ids(self, gateway, ids):
        if not ids:
            return self.none()

        return self.filter(gateway=gateway, id__in=ids)

    def filter_valid_ids(self, gateway, ids):
        return list(self.filter(gateway=gateway, id__in=ids).values_list("id", flat=True))

    def get_latest_resource(self, gateway_id):
        return self.filter(gateway_id=gateway_id).order_by("-updated_time").first()

    def filter_resource_path_method_to_id(self, gateway_id):
        """
        :return: {
            "/test/": {
                "GET": 1,
            }
        }
        """
        resources = self.filter(gateway_id=gateway_id).values("id", "method", "path")
        path_method_to_id = defaultdict(dict)
        for resource in resources:
            path_method_to_id[resource["path"]][resource["method"]] = resource["id"]
        return path_method_to_id

    def filter_id_to_fields(self, gateway_id: int, fields: List[str]) -> Dict[int, Dict[str, Any]]:
        return {resource["id"]: resource for resource in self.filter(gateway_id=gateway_id).values(*fields)}

    def filter_resource_name_to_id(self, gateway_id):
        return dict(self.filter(gateway_id=gateway_id).values_list("name", "id"))

    def filter_id_is_public_map(self, gateway_id):
        return dict(self.filter(gateway_id=gateway_id).values_list("id", "is_public"))

    def filter_public_resource_ids(self, gateway_id: int) -> List[int]:
        return list(self.filter(gateway_id=gateway_id, is_public=True).values_list("id", flat=True))

    def filter_id_object_map(self, gateway_id):
        return {obj.id: obj for obj in self.filter(gateway_id=gateway_id)}

    def filter_resource_names(self, gateway_id, ids):
        if not ids:
            return []

        return list(self.filter(gateway_id=gateway_id, id__in=ids).values_list("name", flat=True))

    def get_id_to_fields_map(self, resource_ids: List[int]) -> Dict[int, dict]:
        if not resource_ids:
            return {}

        return {
            r["id"]: dict(r, api_name=r["gateway__name"])
            for r in self.filter(id__in=resource_ids).values(
                "id", "name", "description", "gateway_id", "gateway__name"
            )
        }

    def get_id_to_name(self, gateway_id: int, resource_ids: Optional[List[int]] = None) -> Dict[int, str]:
        qs = self.filter(gateway_id=gateway_id)

        if resource_ids is not None:
            qs = qs.filter(id__in=resource_ids)

        return dict(qs.values_list("id", "name"))

    def group_by_api_id(self, resource_ids: List[int]) -> Dict[int, List[int]]:
        data = self.filter(id__in=resource_ids).values("gateway_id", "id").order_by("gateway_id")
        return {
            gateway_id: [item["id"] for item in group]
            for gateway_id, group in itertools.groupby(data, key=operator.itemgetter("gateway_id"))
        }

    def get_unspecified_resource_fields(self, gateway_id: int, ids: List[int]) -> List[Dict[str, Any]]:
        """获取指定网关下，未在指定 ids 中的资源的一些字段数据"""
        return list(self.filter(gateway_id=gateway_id).exclude(id__in=ids).values("id", "name", "method", "path"))

    def get_resource_ids_by_names(self, gateway_id: int, resource_names: Optional[List[str]]) -> List[int]:
        if not resource_names:
            return []

        return list(self.filter(gateway_id=gateway_id, name__in=resource_names).values_list("id", flat=True))

    def get_name(self, gateway_id: int, id_: int) -> Optional[str]:
        return self.filter(gateway_id=gateway_id, id=id_).values_list("name", flat=True).first()


class ProxyManager(models.Manager):
    # FIXME: move to biz layer
    def save_proxy_config(
        self,
        resource,
        type,
        config,
        backend_config_type: str = BackendConfigTypeEnum.DEFAULT.value,
        backend_service_id: Optional[int] = None,
    ):
        factory = SchemaFactory()
        return self.update_or_create(
            resource=resource,
            type=type,
            defaults={
                "backend_config_type": backend_config_type,
                "backend_service_id": backend_service_id,
                "config": config,
                "schema": factory.get_proxy_schema(type),
            },
        )

    def get_proxy_type(self, proxy_id):
        """
        获取代理的类型
        """
        return self.get(id=proxy_id).type

    def filter_proxies(self, resource_ids):
        queryset = self.filter(resource_id__in=resource_ids)
        return {
            proxy.id: {
                "type": proxy.type,
                "config": proxy.config,
            }
            for proxy in queryset
        }

    def delete_by_resource_ids(self, resource_ids):
        self.filter(resource_id__in=resource_ids).delete()

    def get_resource_id_to_snapshot(self, resource_ids):
        from apigateway.schema.models import Schema

        schemas = Schema.objects.filter_id_snapshot_map()
        return {
            proxy.resource_id: proxy.snapshot(as_dict=True, schemas=schemas)
            for proxy in self.filter(resource_id__in=resource_ids).prefetch_related("backend")
        }

    def get_backend_resource_count(self, backend_ids: List[int]) -> Dict[int, int]:
        qs = self.filter(backend_id__in=backend_ids).values("backend_id").annotate(count=Count("backend_id"))
        return {i["backend_id"]: i["count"] for i in qs}


class StageResourceDisabledManager(models.Manager):
    def get_disabled_stages(self, resource_id):
        disabled_stages = self.filter(resource_id=resource_id).values("stage__id", "stage__name")
        return [
            {
                "id": stage["stage__id"],
                "name": stage["stage__name"],
            }
            for stage in disabled_stages
        ]

    def is_exists(self, stage_id, resource_id):
        return self.filter(stage__id=stage_id, resource__id=resource_id).exists()

    def delete_enabled_records(self, stage_id, resource_id):
        return self.filter(stage__id=stage_id, resource__id=resource_id).delete()

    def get_record(self, stage_id, resource_id):
        return self.get(stage__id=stage_id, resource__id=resource_id)

    def get_or_new_record(self, stage_id, resource_id):
        if self.is_exists(stage_id, resource_id):
            return self.get_record(stage_id, resource_id)

        record = self.model()
        record.stage_id = stage_id
        record.resource_id = resource_id

        return record


class ResourceVersionManager(models.Manager):
    def get_latest_version(self, gateway_id: int):
        """
        网关最新的版本
        """
        return self.filter(gateway_id=gateway_id).last()

    # TODO: 缓存优化：可使用 django cache(with database backend) or dogpile 缓存
    # 版本中包含的配置不会变化，但是处理逻辑可能调整，因此，缓存需支持版本
    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_LONG.value))
    def get_used_stage_vars(self, gateway_id, id):
        resoruce_version = self.filter(gateway_id=gateway_id, id=id).first()
        if not resoruce_version:
            return None

        used_in_path = set()
        used_in_host = set()
        for resource in resoruce_version.data:
            if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
                continue

            proxy_config = json.loads(resource["proxy"]["config"])

            proxy_path = proxy_config["path"]
            used_in_path.update(STAGE_VAR_PATTERN.findall(proxy_path))

            proxy_upstreams = proxy_config.get("upstreams")
            if proxy_upstreams:
                # 覆盖环境配置
                used_in_host.update(
                    STAGE_VAR_PATTERN.findall(";".join([host["host"] for host in proxy_upstreams["hosts"]]))
                )

        return {
            "in_path": list(used_in_path),
            "in_host": list(used_in_host),
        }

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_LONG.value))
    def has_used_stage_upstreams(self, gateway_id: int, id: int) -> bool:
        """资源 Hosts 是否存在使用默认配置"""
        resoruce_version = self.filter(gateway_id=gateway_id, id=id).first()
        for resource in resoruce_version.data:
            if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
                continue

            proxy_config = json.loads(resource["proxy"]["config"])
            proxy_upstreams = proxy_config.get("upstreams")
            if not proxy_upstreams:
                return True

        return False

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_LONG.value))
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
                "description": resource.get("description", ""),
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

    def get_release_by_stage_id(self, stage_id):
        return self.filter(stage_id=stage_id).all()

    def get_release_by_gateway_id(self, gateway_id):
        return self.filter(gateway_id=gateway_id).all()

    def filter_released_gateway_ids(self, gateway_ids):
        return set(self.filter(gateway_id__in=gateway_ids).values_list("gateway_id", flat=True))

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

    def get_released_stage_count(self, resource_version_ids: List[int]) -> Dict[int, int]:
        """获取资源版本已发布的环境数量"""
        count = (
            self.filter(resource_version_id__in=resource_version_ids)
            .values("resource_version_id")
            .annotate(count=Count("resource_version_id"))
        )
        return {i["resource_version_id"]: i["count"] for i in count}

    def get_stage_id_to_fields_map(
        self,
        gateway_id: int,
        resource_version_ids: Optional[List[int]] = None,
    ) -> Dict[int, dict]:
        """获取已发布环境的信息"""
        queryset = self.filter(gateway_id=gateway_id)
        if resource_version_ids is not None:
            queryset = queryset.filter(resource_version_id__in=resource_version_ids)

        return {release["stage_id"]: dict(release) for release in queryset.values("stage_id", "resource_version_id")}

    def get_stage_ids_unreleased_the_version(
        self,
        gateway_id: int,
        stage_ids: List[int],
        resource_version_id: int,
    ) -> List[int]:
        """获取未发布此版本的环境列表"""
        released_stage_ids = self.filter(
            gateway_id=gateway_id,
            resource_version_id=resource_version_id,
        ).values_list("stage_id", flat=True)
        return list(set(stage_ids) - set(released_stage_ids))


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

    def get_resource_version_id_to_obj_map(self, gateway_id: int, resource_id: int):
        """获取已发布资源版本 ID 对应的发布资源"""
        return {
            resource.resource_version_id: resource
            for resource in self.filter(gateway_id=gateway_id, resource_id=resource_id)
        }

    def get_released_resource(self, gateway_id: int, resource_version_id: int, resource_name: str) -> Optional[dict]:
        released_resource = self.filter(
            gateway_id=gateway_id,
            resource_version_id=resource_version_id,
            resource_name=resource_name,
        ).first()
        if not released_resource:
            return None

        return self._parse_released_resource(released_resource)

    def get_latest_released_resource(self, gateway_id: int, resource_id: int) -> dict:
        """获取资源最新的发布配置"""
        released_resource = (
            self.filter(gateway_id=gateway_id, resource_id=resource_id).order_by("-resource_version_id").first()
        )
        if not released_resource:
            return {}

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
            "description": resource.get("description", ""),
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
                Q(stages__name__contains=query)
                | Q(resource_version__name__contains=query)
                | Q(resource_version__title__contains=query)
                | Q(resource_version__version__contains=query)
            )

        if stage_id:
            queryset = queryset.filter(stages__id=stage_id)

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

    def get_recent_releasers(self, gateway_id: int) -> List[str]:
        qs = self.filter(gateway_id=gateway_id).order_by("-id")[:10]
        return list(set(qs.values_list("created_by", flat=True)))


class PublishEventManager(models.Manager):
    pass


class ContextManager(models.Manager):
    def save_config(self, scope_type, scope_id, type, config, schema):
        return self.update_or_create(
            scope_type=scope_type,
            scope_id=scope_id,
            type=type,
            defaults={
                "config": config,
                "schema": schema,
            },
        )

    def get_config(self, scope_type, scope_id, type):
        return self.get(scope_type=scope_type, scope_id=scope_id, type=type).config

    def delete_by_scope_ids(self, scope_type, scope_ids):
        self.filter(scope_type=scope_type, scope_id__in=scope_ids).delete()


class JWTManager(models.Manager):
    def create_jwt(self, gateway):
        private_key, public_key = KeyGenerator().generate_rsa_key()
        cipher = AESCipherManager.create_jwt_cipher()
        return self.create(
            gateway=gateway,
            # 使用加密数据，不保存明文的 private_key
            # private_key=smart_str(private_key),
            private_key="",
            public_key=smart_str(public_key),
            encrypted_private_key=cipher.encrypt_to_hex(smart_str(private_key)),
        )

    def update_jwt_key(self, gateway, private_key: bytes, public_key: bytes):
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = self.get(gateway=gateway)
        jwt.public_key = smart_str(public_key)
        jwt.encrypted_private_key = cipher.encrypt_to_hex(smart_str(private_key))
        jwt.save(update_fields=["public_key", "encrypted_private_key"])

    def get_private_key(self, gateway_id: int) -> str:
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = self.get(gateway_id=gateway_id)
        return cipher.decrypt_from_hex(jwt.encrypted_private_key)

    def get_jwt(self, gateway):
        try:
            return self.get(gateway=gateway)
        except Exception:
            raise error_codes.NOT_FOUND.format(_("网关密钥不存在。"), replace=True)

    def is_jwt_key_changed(self, gateway, private_key: bytes, public_key: bytes) -> bool:
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = self.get(gateway=gateway)
        return jwt.public_key != smart_str(public_key) or cipher.decrypt_from_hex(
            jwt.encrypted_private_key
        ) != smart_str(private_key)


class APIRelatedAppManager(models.Manager):
    def allow_app_manage_gateway(self, gateway_id: int, bk_app_code: str) -> bool:
        """是否允许应用管理网关"""
        return self.filter(gateway_id=gateway_id, bk_app_code=bk_app_code).exists()

    def add_related_app(self, gateway_id: int, bk_app_code: str):
        """添加关联应用"""

        # 检查app能关联的网关最大数量
        self._check_app_gateway_limit(bk_app_code)

        self.get_or_create(gateway_id=gateway_id, bk_app_code=bk_app_code)

    def _check_app_gateway_limit(self, bk_app_code: str):
        max_gateway_per_app = settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"].get(
            bk_app_code, settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app"]
        )
        if self.filter(bk_app_code=bk_app_code).count() >= max_gateway_per_app:
            raise error_codes.INVALID_ARGUMENT.format(
                f"The app [{bk_app_code}] exceeds the limit of the number of gateways that can be related."
                + f" The maximum limit is {max_gateway_per_app}."
            )


class MicroGatewayManager(models.Manager):
    def get_id_to_fields(self, ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        if not ids:
            return {}

        return {item["id"]: item for item in self.filter(id__in=ids).values("id", "name")}

    def get_default_shared_gateway(self):
        return self.get(is_shared=True, id=settings.DEFAULT_MICRO_GATEWAY_ID)

    def get_count_by_gateway(self, gateway_ids: List[int]) -> Dict[int, int]:
        if not gateway_ids:
            return {}

        count = self.filter(gateway_id__in=gateway_ids).values("gateway_id").annotate(count=Count("gateway_id"))
        return {i["gateway_id"]: i["count"] for i in count}


class BackendServiceManager(models.Manager):
    def delete_backend_service(self, id: int):
        self._precheck_delete_instance(id)
        self.filter(id=id).delete()

    def _precheck_delete_instance(self, id: int):
        from apigateway.core.models import Proxy

        proxy = Proxy.objects.filter(backend_service_id=id).first()
        if not proxy:
            return

        raise InstanceDeleteError(
            _("后端服务【id={id}】被资源【id={resource_id}】引用，无法删除。").format(id=id, resource_id=proxy.resource_id)
        )


class SslCertificateManager(models.Manager):
    def delete_by_gateway_id(self, gateway_id: int):
        from apigateway.core.models import SslCertificateBinding

        # delete binding
        SslCertificateBinding.objects.filter(gateway_id=gateway_id).delete()

        # delete ssl-certificate
        self.filter(gateway_id=gateway_id).delete()

    def delete_by_id(self, id: int):
        self._check_for_delete(id)
        self.filter(id=id).delete()

    def _check_for_delete(self, id: int):
        """检查是否能被删除"""
        from apigateway.core.models import SslCertificateBinding

        binding = SslCertificateBinding.objects.filter(ssl_certificate_id=id).first()
        if not binding:
            return

        scope_label = SSLCertificateBindingScopeTypeEnum.get_choice_label(binding.scope_type)
        raise InstanceDeleteError(
            _("SSL 证书【id={id}】被 {scope_label}【id={scope_id}】引用，无法删除。").format(
                id=id,
                scope_label=scope_label,
                scope_id=binding.scope_id,
            )
        )

    def get_valid_ids(self, gateway_id: int, ids: List[int]) -> List[int]:
        return list(self.filter(gateway_id=gateway_id, id__in=ids).values_list("id", flat=True))

    def get_valid_id(self, gateway_id: int, id_: int) -> Optional[int]:
        return self.filter(gateway_id=gateway_id, id=id_).values_list("id", flat=True).first()


class SslCertificateBindingManager(models.Manager):
    def sync_binding(
        self,
        gateway_id: int,
        scope_type: SSLCertificateBindingScopeTypeEnum,
        scope_id: int,
        ssl_certificate_id: Optional[int],
    ):
        """同步绑定关系，将新增，更新或删除绑定关系，保持其与实际一致"""
        if not ssl_certificate_id:
            self.filter(gateway_id=gateway_id, scope_type=scope_type.value, scope_id=scope_id).delete()
            return

        self.update_or_create(
            gateway_id=gateway_id,
            scope_type=scope_type.value,
            scope_id=scope_id,
            defaults={
                "ssl_certificate_id": ssl_certificate_id,
            },
        )

    def get_scope_objects(self, gateway_id: int, scope_type: str, scope_ids: List[int]):
        if scope_type == SSLCertificateBindingScopeTypeEnum.STAGE.value:
            from apigateway.core.models import Stage

            return Stage.objects.filter(gateway_id=gateway_id, id__in=scope_ids)

        raise error_codes.INVALID_ARGUMENT.format(f"unsupported scope_type: {scope_type}")

    def get_valid_scope_ids(self, gateway_id: int, scope_type: str, scope_ids: List[int]) -> List[int]:
        scope_objects = self.get_scope_objects(gateway_id, scope_type, scope_ids)
        return list(scope_objects.values_list("id", flat=True))

    def get_valid_scope_id(self, gateway_id: int, scope_type: str, scope_id: int) -> Optional[int]:
        scope_objects = self.get_scope_objects(gateway_id, scope_type, [scope_id])
        return scope_objects.values_list("id", flat=True).first()
