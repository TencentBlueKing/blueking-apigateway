#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import logging
from typing import Tuple

from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.registry.etcd import EtcdRegistry
from apigateway.controller.release_logger import ReleaseProcedureLogger
from apigateway.controller.transformer import GatewayApisixResourceTransformer, GlobalApisixResourceTransformer
from apigateway.core.models import Gateway, Release, Stage

from .key_prefix import GatewayKeyPrefixHandler, GlobalKeyPrefixHandler

logger = logging.getLogger(__name__)


class SyncFail(Exception):
    """同步失败"""

    def __init__(self, resources):
        self.resources = resources

    def __str__(self):
        return f"sync resources failed: {self.resources}"


# global distributor is full sync
class GlobalResourceDistributor(BaseDistributor):
    def _get_registry(self) -> EtcdRegistry:
        key_prefix = GlobalKeyPrefixHandler().get_release_key_prefix()
        return EtcdRegistry(key_prefix=key_prefix)

    def distribute(
        self,
        release_task_id: str,
        publish_id: int,
    ) -> Tuple[bool, str]:
        """将 release 发布到 global registry 中"""
        transformer = GlobalApisixResourceTransformer()
        registry = self._get_registry()

        gateway = Gateway(id=-1, name="global")
        stage = Stage(id=-1, name="global")

        procedure_logger = ReleaseProcedureLogger(
            "global-distributing",
            logger=logger,
            gateway=gateway,
            stage=stage,
            release_task_id=release_task_id,
            publish_id=publish_id,
        )

        try:
            # step 1: 将网关资源转换为 apisix 资源
            with procedure_logger.step("convert to global apisix resources"):
                transformer.transform()

            resources = list(transformer.get_transformed_resources())

            # step 2: 将 apisix 资源同步到 etcd
            with procedure_logger.step(f"sync global resources(count={len(resources)}) to etcd"):
                fail_resources = registry.sync_resources_by_key_prefix(resources)
                if fail_resources:
                    raise SyncFail(fail_resources)
        except Exception as e:  # pylint: disable=broad-except
            fail_msg = f"distribute global resources to etcd failed: {type(e).__name__}: {str(e)}"
            procedure_logger.exception(fail_msg)
            return False, fail_msg
        return True, ""

    def revoke(
        self,
        release_task_id: str,
        publish_id: int,
    ) -> Tuple[bool, str]:
        raise NotImplementedError()


class GatewayResourceDistributor(BaseDistributor):
    def __init__(self, release: Release):
        self.release = release

    @property
    def gateway(self) -> Gateway:
        return self.release.gateway

    @property
    def stage(self) -> Stage:
        return self.release.stage

    def _get_registry(self, gateway: Gateway, stage: Stage) -> EtcdRegistry:
        key_prefix = GatewayKeyPrefixHandler().get_release_key_prefix(gateway.name, stage.name)
        return EtcdRegistry(key_prefix=key_prefix)

    def distribute(
        self,
        release_task_id: str,
        publish_id: int,
    ) -> Tuple[bool, str]:
        """将 release 发布到 micro-gateway 对应的 registry 中"""
        transformer = GatewayApisixResourceTransformer(
            release=self.release,
            publish_id=publish_id,
        )
        registry = self._get_registry(self.gateway, self.stage)
        procedure_logger = ReleaseProcedureLogger(
            "gateway-distributing",
            logger=logger,
            gateway=self.gateway,
            stage=self.stage,
            release_task_id=release_task_id,
            publish_id=publish_id,
        )

        try:
            # step 1: 将网关资源转换为 apisix 资源
            with procedure_logger.step("convert to gateway apisix resources"):
                transformer.transform()

            resources = list(transformer.get_transformed_resources())

            # step 2: 将 apisix 资源同步到 etcd
            with procedure_logger.step(f"sync gateway resources(count={len(resources)}) to etcd"):
                fail_resources = registry.sync_resources_by_key_prefix(resources)
                if fail_resources:
                    raise SyncFail(fail_resources)
        except Exception as e:  # pylint: disable=broad-except
            fail_msg = f"distribute gateway resources to etcd failed: {type(e).__name__}: {str(e)}"
            procedure_logger.exception(fail_msg)
            return False, fail_msg

        # FIXME: enable this part after v1.20, in v1.21 or v1.22
        # try:
        #     # {self.prefix}/{micro_gateway_name}/{gateway_name}/{stage_name}/{self.api_version}/
        #     # settings.BK_GATEWAY_ETCD_NAMESPACE_PREFIX, default, release.gateway.name, release.stage.name, v1beta1
        #     from django.conf import settings

        #     legacy_key_prefix = f"{settings.BK_GATEWAY_ETCD_NAMESPACE_PREFIX}/default/{release.gateway.name}/{release.stage.name}/v1beta1/"
        #     r = EtcdRegistry(key_prefix=legacy_key_prefix)
        #     r.delete_resources_by_key_prefix()
        # except Exception as e:  # pylint: disable=broad-except
        #     logger.exception(
        #         "delete previous v1beta1 resources from apigw etcd failed: %s: %s", type(e).__name__, str(e)
        #     )
        #     # do nothing

        return True, ""

    def revoke(
        self,
        release_task_id: str,
        publish_id: int,
    ) -> Tuple[bool, str]:
        """撤销已发布到 micro-gateway 对应的 registry 中的配置"""
        registry = self._get_registry(self.gateway, self.stage)

        # 删除所有相关数据
        if publish_id == DELETE_PUBLISH_ID:
            try:
                registry.delete_resources_by_key_prefix()
            except Exception as e:  # pylint: disable=broad-except
                fail_msg = f"revoke gateway resources delete resources from etcd failed: {type(e).__name__}: {str(e)}"
                logger.exception(fail_msg)
                return False, fail_msg
            return True, ""

        procedure_logger = ReleaseProcedureLogger(
            "gateway-revoking",
            logger=logger,
            gateway=self.gateway,
            stage=self.stage,
            release_task_id=release_task_id,
            publish_id=publish_id,
        )

        transformer = GatewayApisixResourceTransformer(
            release=self.release,
            publish_id=publish_id,
            revoke_flag=True,
        )

        try:
            with procedure_logger.step(f"delete gateway resources from etcd by key_prefix({registry.key_prefix})"):
                registry.delete_resources_by_key_prefix()

                # 删除资源后需要同步虚拟路由到 etcd
                transformer.transform()
                resources = list(transformer.get_transformed_resources())
                with procedure_logger.step(f"sync gateway version resources(count={len(resources)}) to etcd"):
                    fail_resources = registry.sync_resources_by_key_prefix(resources)
                    if fail_resources:
                        raise SyncFail(fail_resources)
        except Exception as e:  # pylint: disable=broad-except
            fail_msg = f"revoke gateway resources from etcd failed: {type(e).__name__}: {str(e)}"
            procedure_logger.exception(fail_msg)
            return False, fail_msg

        procedure_logger.info("revoke gateway resources from etcd succeeded")
        return True, ""
