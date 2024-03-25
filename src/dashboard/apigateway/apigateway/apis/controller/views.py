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
import logging
import time
from typing import Optional

from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.controller.permissions import MicroGatewayInstancePermission
from apigateway.apis.controller.serializers import MicroGatewayInfoOutputSLZ, MicroGatewayStatusInputSLZ
from apigateway.controller.constants import MicroGatewayStatusCodeEnum
from apigateway.controller.micro_gateway_config import MicroGatewayBcsInfo
from apigateway.core.models import Gateway, MicroGateway
from apigateway.utils.responses import OKJsonResponse

logger = logging.getLogger(__name__)

PERMISSION_CACHE_DURATION = 60


class MicroGatewayApiMixin:
    def get_micro_gateway(self, instance_id):
        return get_object_or_404(MicroGateway, pk=instance_id)

    def get_related_gateway(self, micro_gateway: MicroGateway, bk_gateway_name: Optional[str] = None):
        qs = Gateway.objects.all().order_by("id")

        if micro_gateway.is_shared and bk_gateway_name:
            qs = qs.filter(name=bk_gateway_name)
        else:
            qs = qs.filter(id=micro_gateway.gateway_id)

        return get_object_or_404(qs)


class MicroGatewayStatusUpdateApi(generics.UpdateAPIView, MicroGatewayApiMixin):
    permission_classes = [MicroGatewayInstancePermission]
    serializer_class = MicroGatewayStatusInputSLZ

    @swagger_auto_schema(
        operation_description="上报微网关的状态",
        tags=["OpenAPI.MicroGateway"],
    )
    def put(self, request, instance_id):
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

        return OKJsonResponse()


class MicroGatewayInfoRetrieveApi(generics.RetrieveAPIView, MicroGatewayApiMixin):
    """查询微网关实例信息"""

    permission_classes = [MicroGatewayInstancePermission]

    @swagger_auto_schema(
        operation_description="获取微网关信息",
        responses={status.HTTP_200_OK: MicroGatewayInfoOutputSLZ},
        tags=["OpenAPI.MicroGateway"],
    )
    def get(self, request, instance_id):
        micro_gateway = self.get_micro_gateway(instance_id)
        related_gateways = micro_gateway.query_related_gateways()

        slz = MicroGatewayInfoOutputSLZ(
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

        return OKJsonResponse(data=slz.data)
