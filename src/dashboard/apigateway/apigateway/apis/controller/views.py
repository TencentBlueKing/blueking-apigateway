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
import json
import logging
import time
from hashlib import md5
from typing import Any, Dict, List, Optional, Tuple

import redis
from django.db.models.signals import post_save
from django.http.response import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.viewsets import GenericViewSet

from apigateway.apis.controller.permissions import MicroGatewayInstancePermission
from apigateway.apis.controller.serializers import (
    MicroGatewayApiPermissionSLZ,
    MicroGatewayAppPermissionQuerySLZ,
    MicroGatewayAppPermissionSLZ,
    MicroGatewayInfoSLZ,
    MicroGatewayNewestGatewayPermissionQuerySLZ,
    MicroGatewayNewestResourcePermissionQuerySLZ,
    MicroGatewayResourcePermissionSLZ,
    MicroGatewayStatusSLZ,
)
from apigateway.apps.permission.models import AppAPIPermission, AppResourcePermission
from apigateway.controller.constants import MicroGatewayStatusCodeEnum
from apigateway.core.micro_gateway_config import MicroGatewayBcsInfo
from apigateway.core.models import Gateway, MicroGateway, Release, Stage
from apigateway.utils.redis_utils import get_default_redis_client, get_redis_key
from apigateway.utils.responses import V1OKJsonResponse

logger = logging.getLogger(__name__)

PERMISSION_CACHE_DURATION = 60


class BaseMicroGatewayViewSet(GenericViewSet):
    permission_classes = [MicroGatewayInstancePermission]

    def get_micro_gateway(self, instance_id):
        return get_object_or_404(MicroGateway, pk=instance_id)

    def get_related_gateway(self, micro_gateway: MicroGateway, bk_gateway_name: Optional[str] = None):
        qs = Gateway.objects.all().order_by("id")

        if micro_gateway.is_shared and bk_gateway_name:
            qs = qs.filter(name=bk_gateway_name)
        else:
            qs = qs.filter(id=micro_gateway.gateway_id)

        return get_object_or_404(qs)


class MicroGatewayStatusViewSet(BaseMicroGatewayViewSet):
    serializer_class = MicroGatewayStatusSLZ

    @swagger_auto_schema(
        operation_description="上报微网关的状态",
        tags=["OpenAPI.MicroGateway"],
    )
    def refresh(self, request, instance_id):
        """
        更新微网关状态，因为微网关上报的状态是直接上报多个副本的状态的，因此这个接口需要汇总出一个状态
        以下条件全部满足时，认为是成功的：
        - 网关信息完全一致
        - 副本信息完全一致
        - 如果有一个副本还正常工作（数据面和控制面状态码皆为 OK），则认为是正常的
        """
        # FIXME: 此处引入是为了适配 python3.6，升级后应该提到最上方
        from apigateway.apis.controller.measurement import MicroGatewayStatus, MicroGatewayStatusMeasurementPoint
        from apigateway.utils.measurement import Measurement

        slz = self.get_serializer(data=request.data)

        slz.is_valid(raise_exception=True)
        gateway_instance = self.get_micro_gateway(instance_id)
        status = MicroGatewayStatus.OK

        gateway = slz.validated_data["gateway"]
        bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(gateway_instance.config)
        # 网关信息判断
        if bcs_info.namespace != gateway["namespace"]:
            status |= MicroGatewayStatus.BASIC_INFO_ERROR

        replica_count = len(slz.validated_data["replicas"])
        if replica_count == 0:
            # 不应该有这样的情况
            status |= MicroGatewayStatus.UNKNOWN_ERROR

        # 缩写约定：cp(control plane)，dp(data plane)
        cp_version_set = set()
        cp_status_code = MicroGatewayStatusCodeEnum.OK.value
        cp_failure_replicas = 0
        dp_version_set = set()
        dp_type_set = set()
        dp_status_code = MicroGatewayStatusCodeEnum.OK.value
        dp_failure_replicas = 0
        success_replicas = 0
        for replicas in slz.validated_data["replicas"]:
            # 收集副本基础信息
            cp_version_set.add(replicas["control_plane_version"])
            dp_version_set.add(replicas["data_plane_version"])
            dp_type_set.add(replicas["data_plane_type"])

            is_replicas_ok = True
            # 当前副本控制面状态
            if replicas["control_plane_status_code"] != MicroGatewayStatusCodeEnum.OK.value:
                # 因数据结构限制，只取其中一个不正常的副本状态
                cp_status_code = replicas["control_plane_status_code"]
                cp_failure_replicas += 1
                is_replicas_ok = False

            # 当前副本数据面状态
            if replicas["data_plane_status_code"] != MicroGatewayStatusCodeEnum.OK.value:
                # 因数据结构限制，只取其中一个不正常的副本状态
                dp_status_code = replicas["data_plane_status_code"]
                dp_failure_replicas += 1
                is_replicas_ok = False

            if is_replicas_ok:
                # 当前副本正常工作
                success_replicas += 1

        # 所有副本版本是否一致
        if len(cp_version_set) != 1:
            status |= MicroGatewayStatus.BASIC_INFO_ERROR | MicroGatewayStatus.CONTROL_PLANE_ERROR
        # 所有副本数据面类型是否一致
        if len(dp_type_set) != 1:
            status |= MicroGatewayStatus.BASIC_INFO_ERROR | MicroGatewayStatus.DATA_PLANE_ERROR
        # 是否有一个副本正常工作
        if success_replicas == 0:
            status |= MicroGatewayStatus.GATEWAY_ERROR

        measurement = Measurement(point_type=MicroGatewayStatusMeasurementPoint)
        measurement.update(
            MicroGatewayStatusMeasurementPoint(
                timestamp=int(time.time() * 1000),
                name=f"{gateway_instance.pk}",
                status=status,
                replicas=replica_count,
                success_replicas=success_replicas,
                control_plane_failures=cp_failure_replicas,
                control_plane_status=cp_status_code,
                data_plane_failures=dp_failure_replicas,
                data_plane_status=dp_status_code,
            )
        )

        return V1OKJsonResponse()


class MicroGatewayPermissionViewSet(BaseMicroGatewayViewSet):
    """查询微网关权限信息"""

    def _get_released_resource_name_mappings(self, release: Release) -> Dict[int, str]:
        return {resource["id"]: resource["name"] for resource in release.resource_version.data}

    def _get_resource_permissions(
        self,
        gateway: Gateway,
        stage: Stage,
        app_code_list: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """根据 Resource Version 来获取真实生效的资源名称"""
        resource_permissions: List[Dict[str, Any]] = []

        release = Release.objects.filter(gateway=gateway, stage=stage).last()
        if not release:
            return resource_permissions

        name_mappings = self._get_released_resource_name_mappings(release)
        queryset = AppResourcePermission.objects.filter(gateway=gateway)
        if app_code_list:
            queryset = queryset.filter(bk_app_code__in=app_code_list)
        for permission in queryset:
            # 因为 resource_version 为下发生效的真实版本，因此没有匹配的权限无需下发
            if permission.resource_id not in name_mappings:
                continue

            resource_permissions.append(
                {
                    "created_time": permission.created_time,
                    "updated_time": permission.updated_time,
                    "expires": permission.expires,
                    "bk_app_code": permission.bk_app_code,
                    "resource_name": name_mappings[permission.resource_id],
                }
            )

        return resource_permissions

    def _get_api_permissions(self, gateway: Gateway, app_code_list: Optional[List[str]]):
        qs = AppAPIPermission.objects.filter(gateway=gateway)
        if app_code_list:
            qs = qs.filter(bk_app_code__in=app_code_list)

        return qs

    def _get_cache_key(
        self, micro_gateway: MicroGateway, gateway: Gateway, stage: Stage, app_code_list: Optional[List[str]]
    ) -> str:
        key = get_redis_key(f"permission::{micro_gateway.pk}::{gateway.pk}::{stage.name}")
        if not app_code_list:
            return key

        app_md5 = md5()
        for i in app_code_list:
            app_md5.update(i.encode())

        return f"{key}::{app_md5.hexdigest()}"

    def _get_permissions_from_db(
        self,
        gateway: Gateway,
        stage: Stage,
        app_code_list: Optional[List[str]],
    ) -> Dict[str, Any]:
        result_slz = MicroGatewayAppPermissionSLZ(
            {
                "gateway_name": gateway.name,
                "stage_name": stage.name,
                "resource_permissions": self._get_resource_permissions(gateway, stage, app_code_list),
                "api_permissions": self._get_api_permissions(gateway, app_code_list),
            },
        )
        return result_slz.data

    def _get_permissions_from_cache(self, client: redis.Redis, cache_key: str) -> Tuple[Optional[Dict[str, Any]], int]:
        pipeline = client.pipeline()
        pipeline.get(cache_key)
        pipeline.ttl(cache_key)
        try:
            cached, ttl = pipeline.execute()
        except Exception:
            logger.exception("query from cache %s failed, skip", cache_key)
            return None, 0

        if not cached:
            return None, 0

        try:
            loaded = json.loads(cached)
        except Exception:
            logger.exception("load cached result %s failed", cache_key)
            return None, 0

        return loaded, ttl

    def _set_permissions_into_cache(self, client: redis.Redis, cache_key: str, queried: Dict[str, Any], expires: int):
        try:
            client.set(cache_key, json.dumps(queried), ex=expires)
        except Exception:
            logger.exception("abort set permissions into cache %s", cache_key)

    def _get_stage_by_name(self, gateway: Gateway, stage_name: str) -> Stage:
        return get_object_or_404(Stage, gateway=gateway, name=stage_name)

    @swagger_auto_schema(
        operation_description="获取微网关的所有权限信息",
        query_serializer=MicroGatewayAppPermissionQuerySLZ,
        responses={status.HTTP_200_OK: MicroGatewayAppPermissionSLZ},
        tags=["OpenAPI.MicroGateway"],
    )
    def list(self, request, instance_id):
        slz = MicroGatewayAppPermissionQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        gateway_name = slz.validated_data["gateway_name"]
        stage_name = slz.validated_data["stage_name"]
        app_code_list = slz.validated_data.get("target_app_code")
        micro_gateway = self.get_micro_gateway(instance_id)
        gateway = self.get_related_gateway(micro_gateway, gateway_name)
        stage = self._get_stage_by_name(gateway, stage_name)

        # NOTE: key should contains stage.name, while the _get_permissions_from_db() use stage as a parameter
        cache_key = self._get_cache_key(micro_gateway, gateway, stage, app_code_list)
        redis_client = get_default_redis_client()

        cached, _ = self._get_permissions_from_cache(redis_client, cache_key)
        if cached is not None:
            return V1OKJsonResponse(data=cached)

        queried = self._get_permissions_from_db(gateway, stage, app_code_list)
        # 考虑到微网关一般都是多副本的，权限查询请求容易有热点
        # 因此将权限查询结果缓存到 redis 一分钟，优化查询速度
        self._set_permissions_into_cache(redis_client, cache_key, queried, PERMISSION_CACHE_DURATION)

        return V1OKJsonResponse(data=queried)


class MicroGatewayNewestPermissionViewSet(BaseMicroGatewayViewSet):
    @classmethod
    def get_related_gateway_permission_fast_cache_key(cls, gateway_id: int, app_code: str) -> str:
        return get_redis_key(f"fast-permission::{gateway_id}::api::{app_code}")

    @classmethod
    def get_resource_permission_fast_cache_key(cls, gateway_id: int, resource_name: str, app_code: str) -> str:
        return get_redis_key(f"fast-permission::{gateway_id}::resource::{resource_name}::{app_code}")

    @classmethod
    def _set_fast_permission_cache(cls, cache_key: str, cache_value: Dict[str, Any]):
        redis_client = get_default_redis_client()
        redis_client.setex(cache_key, 2 * PERMISSION_CACHE_DURATION, json.dumps(cache_value))

    @classmethod
    def _fast_set_api_permission_cache(cls, instance: AppAPIPermission, created: bool, **kwargs):
        slz = MicroGatewayApiPermissionSLZ(instance)

        cls._set_fast_permission_cache(
            cls.get_related_gateway_permission_fast_cache_key(instance.gateway_id, instance.bk_app_code),
            slz.data,
        )

    @classmethod
    def _fast_set_resource_permission_cache(cls, instance: AppResourcePermission, created: bool, **kwargs):
        resource = instance.resource
        if not resource:
            return

        slz = MicroGatewayResourcePermissionSLZ(instance)
        cache_value = slz.data
        cache_value["resource_name"] = resource.name

        cls._set_fast_permission_cache(
            cls.get_resource_permission_fast_cache_key(instance.gateway_id, resource.name, instance.bk_app_code),
            cache_value,
        )

    @swagger_auto_schema(
        operation_description="获取微网关的新添加网关维度权限信息",
        query_serializer=MicroGatewayNewestGatewayPermissionQuerySLZ,
        responses={status.HTTP_200_OK: MicroGatewayAppPermissionSLZ},
        tags=["OpenAPI.MicroGateway"],
    )
    def list_newest_gateway_permissions(self, request, instance_id):
        slz = MicroGatewayNewestGatewayPermissionQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        gateway_name = slz.validated_data["gateway_name"]
        stage_name = slz.validated_data.get("stage_name")
        app_code_list = slz.validated_data["target_app_code"]
        micro_gateway = self.get_micro_gateway(instance_id)
        gateway = self.get_related_gateway(micro_gateway, gateway_name)

        if gateway_name != gateway.name:
            return HttpResponseForbidden()

        redis_client = get_default_redis_client()
        pipeline = redis_client.pipeline()
        for app_code in app_code_list:
            pipeline.get(self.get_related_gateway_permission_fast_cache_key(gateway.pk, app_code))

        result_slz = MicroGatewayAppPermissionSLZ(
            {
                "gateway_name": gateway.name,
                "stage_name": stage_name,
                "api_permissions": [json.loads(i) for i in pipeline.execute() if i],
            },
        )

        return V1OKJsonResponse(data=result_slz.data)

    @swagger_auto_schema(
        operation_description="获取微网关的新添加资源维度权限信息",
        query_serializer=MicroGatewayNewestResourcePermissionQuerySLZ,
        responses={status.HTTP_200_OK: MicroGatewayAppPermissionSLZ},
        tags=["OpenAPI.MicroGateway"],
    )
    def list_newest_resource_permissions(self, request, instance_id):
        slz = MicroGatewayNewestResourcePermissionQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        gateway_name = slz.validated_data["gateway_name"]
        stage_name = slz.validated_data.get("stage_name")
        resource_name = slz.validated_data["resource_name"]
        app_code_list = slz.validated_data["target_app_code"]
        micro_gateway = self.get_micro_gateway(instance_id)
        gateway = self.get_related_gateway(micro_gateway, gateway_name)

        if gateway_name != gateway.name:
            return HttpResponseForbidden()

        redis_client = get_default_redis_client()
        pipeline = redis_client.pipeline()
        for app_code in app_code_list:
            pipeline.get(self.get_resource_permission_fast_cache_key(gateway.pk, resource_name, app_code))

        result_slz = MicroGatewayAppPermissionSLZ(
            {
                "gateway_name": gateway.name,
                "stage_name": stage_name,
                "resource_permissions": [json.loads(i) for i in pipeline.execute() if i],
            },
        )

        return V1OKJsonResponse(data=result_slz.data)


post_save.connect(
    MicroGatewayNewestPermissionViewSet._fast_set_api_permission_cache,
    sender=AppAPIPermission,
)
post_save.connect(
    MicroGatewayNewestPermissionViewSet._fast_set_resource_permission_cache,
    sender=AppResourcePermission,
)


class MicroGatewayInfoViewSet(BaseMicroGatewayViewSet):
    """查询微网关实例信息"""

    @swagger_auto_schema(
        operation_description="获取微网关信息",
        responses={status.HTTP_200_OK: MicroGatewayInfoSLZ},
        tags=["OpenAPI.MicroGateway"],
    )
    def get(self, request, instance_id):
        micro_gateway = self.get_micro_gateway(instance_id)
        related_gateways = micro_gateway.query_related_gateways()

        slz = MicroGatewayInfoSLZ(
            {
                "name": micro_gateway.name,
                "related_infos": [
                    {
                        "gateway_name": gateway.name,
                        "stage_name": stage.name,
                    }
                    for gateway in related_gateways
                    for stage in gateway.stage_set.all()
                ],
            }
        )

        return V1OKJsonResponse(data=slz.data)
