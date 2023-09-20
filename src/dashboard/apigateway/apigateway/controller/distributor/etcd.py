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
from typing import Optional, Tuple

from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.crds.v1beta1.convertor import CustomResourceConvertor
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.distributor.key_prefix import KeyPrefixHandler
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.controller.registry.etcd import EtcdRegistry
from apigateway.core.models import Gateway, MicroGateway, Release, Stage

logger = logging.getLogger(__name__)


class SyncFail(Exception):
    """同步失败"""

    def __init__(self, resources):
        self.resources = resources

    def __str__(self):
        return f"sync resources failed: {self.resources}"


class EtcdDistributor(BaseDistributor):
    def __init__(self, include_gateway_global_config: bool = False):
        """
        :param include_gateway_global_config: 是否应包含网关全局配置资源，如：BkGatewayConfig, BkGatewayPluginMetadata；
            共享网关，专享网关，当同步对应网关的数据到共享网关集群时，应包含这些网关的全局配置资源
        """
        self.include_gateway_global_config = include_gateway_global_config

    def distribute(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """将 release 发布到 micro-gateway 对应的 registry 中"""
        convertor = CustomResourceConvertor(
            release=release,
            publish_id=publish_id,
            micro_gateway=micro_gateway,
            include_config=self.include_gateway_global_config,
            include_plugin_metadata=self.include_gateway_global_config,
        )
        registry = self._get_registry(release.gateway, release.stage, micro_gateway)
        procedure_logger = ReleaseProcedureLogger(
            "gateway-distributing",
            logger=logger,
            gateway=release.gateway,
            stage=release.stage,
            micro_gateway=micro_gateway,
            release_task_id=release_task_id,
            publish_id=publish_id,
        )

        try:
            # step 1: 将网关资源转换为 kubernetes 资源
            with procedure_logger.step("convert to kubernetes resources"):
                convertor.convert()

            resources = list(convertor.get_kubernetes_resources())

            # step 2: 将 kubernetes 资源同步到 etcd
            with procedure_logger.step(f"sync resources(count={len(resources)}) to etcd"):
                fail_resources = registry.sync_resources_by_key_prefix(resources)
                if fail_resources:
                    raise SyncFail(fail_resources)
        except Exception as e:
            fail_msg = f"distribute to etcd failed: {type(e).__name__}: {str(e)}"
            procedure_logger.exception(fail_msg)
            return False, fail_msg

        return True, ""

    def revoke(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """撤销已发布到 micro-gateway 对应的 registry 中的配置"""
        registry = self._get_registry(release.gateway, release.stage, micro_gateway)

        # 删除所有相关数据
        if publish_id == DELETE_PUBLISH_ID:
            try:
                registry.delete_resources_by_key_prefix()
            except Exception as e:
                fail_msg = f"revoke delete resources from etcd failed: {type(e).__name__}: {str(e)}"
                logger.exception(fail_msg)
                return False, fail_msg
            return True, ""

        procedure_logger = ReleaseProcedureLogger(
            "gateway-revoking",
            logger=logger,
            gateway=release.gateway,
            stage=release.stage,
            micro_gateway=micro_gateway,
            release_task_id=release_task_id,
            publish_id=publish_id,
        )

        convertor = CustomResourceConvertor(
            release=release,
            publish_id=publish_id,
            micro_gateway=micro_gateway,
            revoke_flag=True,
        )

        try:
            with procedure_logger.step(f"delete resources from etcd by key_prefix({registry.key_prefix})"):
                registry.delete_resources_by_key_prefix()

                # 删除资源后需要同步虚拟路由到 etcd
                convertor.convert()
                resources = list(convertor.get_kubernetes_resources())
                with procedure_logger.step(f"sync version resources(count={len(resources)}) to etcd"):
                    fail_resources = registry.sync_resources_by_key_prefix(resources)
                    if fail_resources:
                        raise SyncFail(fail_resources)
        except Exception as e:
            fail_msg = f"revoke resources from etcd failed: {type(e).__name__}: {str(e)}"
            procedure_logger.exception(fail_msg)
            return False, fail_msg

        procedure_logger.info("revoke resources from etcd succeeded")
        return True, ""

    def _get_registry(self, gateway: Gateway, stage: Stage, micro_gateway: MicroGateway) -> EtcdRegistry:
        key_prefix = KeyPrefixHandler().get_release_key_prefix(micro_gateway.name, gateway.name, stage.name)
        return EtcdRegistry(key_prefix=key_prefix)
