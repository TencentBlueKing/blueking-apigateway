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
"""
微网关实例处理器
"""
from abc import ABCMeta, abstractmethod
from typing import Any, Dict

from blue_krill.async_utils.django_utils import delay_on_commit
from django.conf import settings

from apigateway.apps.micro_gateway.constants import MicroGatewayCreateWayEnum
from apigateway.controller.tasks import deploy_micro_gateway
from apigateway.core.constants import MicroGatewayStatusEnum


# FIXME: this is not a good abstract template, should be refactored
class BaseMicroGatewayHandler(metaclass=ABCMeta):
    @abstractmethod
    def deploy(self, micro_gateway_id: int, access_token: str, username: str = ""):
        """部署微网关"""

    def get_initial_status(self) -> MicroGatewayStatusEnum:
        return MicroGatewayStatusEnum.PENDING

    def get_initial_bcs_info(self) -> Dict[str, Any]:
        return {}


class NeedDeployMicroGatewayHandler(BaseMicroGatewayHandler):
    """新部署的微网关实例"""

    def deploy(self, micro_gateway_id: int, access_token: str, username: str = ""):
        delay_on_commit(deploy_micro_gateway, micro_gateway_id, access_token, username)

    def get_initial_bcs_info(self) -> Dict[str, Any]:
        """新部署微网关实例时，使用默认配置的 chart"""
        return {
            "chart_name": settings.BCS_MICRO_GATEWAY_CHART_NAME,
            "chart_version": settings.BCS_MICRO_GATEWAY_CHART_VERSION,
        }


class RelateDeployedMicroGatewayHandler(BaseMicroGatewayHandler):
    """接入已部署的微网关实例"""

    def deploy(self, micro_gateway_id: int, access_token: str, username: str = ""):
        """部署微网关"""

    def get_initial_status(self) -> MicroGatewayStatusEnum:
        return MicroGatewayStatusEnum.INSTALLED


class MicroGatewayHandlerFactory:
    _mapping = {
        MicroGatewayCreateWayEnum.NEED_DEPLOY: NeedDeployMicroGatewayHandler,
        MicroGatewayCreateWayEnum.RELATE_DEPLOYED: RelateDeployedMicroGatewayHandler,
    }

    @classmethod
    def get_handler(cls, create_way: MicroGatewayCreateWayEnum) -> BaseMicroGatewayHandler:
        try:
            handler_cls = cls._mapping[create_way]

            return handler_cls()
        except KeyError:
            raise ValueError(f"unsupported create_way: {create_way.value}")
