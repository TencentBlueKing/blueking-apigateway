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
from typing import Callable, Optional, Type

from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.distributor.etcd import EtcdDistributor
from apigateway.controller.distributor.helm import HelmDistributor
from apigateway.core.models import MicroGateway, Release, Stage

logger = logging.getLogger(__name__)


class CombineDistributor(BaseDistributor):
    def __init__(
        self,
        helm_distributor_type: Type[HelmDistributor] = HelmDistributor,
        etcd_distributor_type: Type[EtcdDistributor] = EtcdDistributor,
    ):
        self.helm_distributor_type = helm_distributor_type
        self.etcd_distributor_type = etcd_distributor_type

    def foreach_distributor(
        self,
        stage: Stage,
        micro_gateway: MicroGateway,
        callback: Callable[[BaseDistributor, MicroGateway], None],
    ):
        """遍历所有的 distributor 并调用回调，除了传入的微网关实例，会判断是否需要同时调用自身托管的实例"""
        # 只处理共享网关
        assert micro_gateway.is_shared

        managed_micro_gateway = stage.micro_gateway
        # 如果微网关不存在, 只发布default共享网关
        if not managed_micro_gateway:
            callback(self.etcd_distributor_type(include_gateway_global_config=False), micro_gateway)
            return

        # NOTE: 发布专享网关时不再同时发布共享网关
        # if managed_micro_gateway != micro_gateway:
        #     # 指定的共享实例
        #     callback(self.etcd_distributor_type(include_gateway_global_config=False), micro_gateway)

        # if not managed_micro_gateway:
        #     return

        # 发布共享网关
        if managed_micro_gateway.is_shared:
            callback(self.etcd_distributor_type(include_gateway_global_config=True), managed_micro_gateway)
            return

        # 发布专享网关
        if managed_micro_gateway.is_managed:
            callback(self.helm_distributor_type(generate_chart=False), managed_micro_gateway)

    def distribute(self, release: Release, micro_gateway: MicroGateway, release_task_id: Optional[str] = None) -> bool:
        has_failure = False

        def do_distribute(distributor: BaseDistributor, gateway: MicroGateway):
            if not distributor.distribute(release, gateway, release_task_id):
                nonlocal has_failure
                has_failure = True

        self.foreach_distributor(release.stage, micro_gateway, do_distribute)
        return not has_failure

    def revoke(self, stage: Stage, micro_gateway: MicroGateway, release_task_id: Optional[str] = None) -> bool:
        has_failure = False

        def do_revoke(distributor: BaseDistributor, gateway: MicroGateway):
            if not distributor.revoke(stage, gateway, release_task_id):
                nonlocal has_failure
                has_failure = True

        self.foreach_distributor(stage, micro_gateway, do_revoke)

        return not has_failure
