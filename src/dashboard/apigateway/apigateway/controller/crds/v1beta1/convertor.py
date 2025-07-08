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
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from apigateway.controller.crds.base import KubernetesResource
from apigateway.controller.crds.release_data.release_data import ReleaseData, ReleaseDataV2
from apigateway.controller.crds.v1beta1.convertors.gateway_config import GatewayConfigConvertor
from apigateway.controller.crds.v1beta1.convertors.plugin_metadata import PluginMetadataConvertor
from apigateway.controller.crds.v1beta1.convertors.resource import HttpResourceConvertor
from apigateway.controller.crds.v1beta1.convertors.service import ServiceConvertor
from apigateway.controller.crds.v1beta1.convertors.stage import StageConvertor
from apigateway.controller.crds.v1beta1.models.gateway_config import BkGatewayConfig
from apigateway.controller.crds.v1beta1.models.gateway_plugin_metadata import BkGatewayPluginMetadata
from apigateway.controller.crds.v1beta1.models.gateway_resource import BkGatewayResource
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService
from apigateway.controller.crds.v1beta1.models.gateway_stage import BkGatewayStage
from apigateway.core.models import MicroGateway, Release

logger = logging.getLogger(__name__)


@dataclass
class CustomResourceConvertor:
    """网关自定义资源转换器"""

    # 为何 Convertor 需要一个中间的 registry？
    # 1. registry 抽象可以让 Convertor 不耦合任何具体类型
    # 2. 转换过程中可以通过 registry 来查询确保引用正确（如 BkgatewayResource.service 字段）

    # 那为何使用中间 registry 而不是最终目标的 registry？
    # 1. 转换过程会持续写入到 registry 中，中途如果遇到数据异常会中断，不保证原子性
    # 2. 转换过程也会从 registry 查询，如果使用目标 registry，会有历史数据的干扰
    # 3. 中间 registry 应该看做目标 registry 的最终状态

    release: Release
    micro_gateway: MicroGateway
    publish_id: Optional[int] = field(default=None)
    # 是否是撤销资源
    revoke_flag: Optional[bool] = field(default=False)
    # 包含哪些资源的开关
    include_config: bool = field(default=True)
    # 默认包含 stage 资源，调用方不需要传
    include_stage: bool = field(default=True)
    include_http_resource: bool = field(default=True)
    include_service: bool = field(default=True)
    include_plugin_metadata: bool = field(default=True)
    # 转换后的资源
    _gateway_config: Optional[BkGatewayConfig] = field(init=False, default=None)
    _stage: Optional[BkGatewayStage] = field(init=False, default=None)
    _services: List[BkGatewayService] = field(init=False, default_factory=list)
    _http_resources: List[BkGatewayResource] = field(init=False, default_factory=list)
    _plugin_metadata: List[BkGatewayPluginMetadata] = field(init=False, default_factory=list)

    def __post_init__(self):
        if self.release.resource_version.is_schema_v2:
            self._release_data = ReleaseDataV2(self.release)
        else:
            self._release_data = ReleaseData(self.release)

    def convert(self):
        self._iter_convert()

    def _iter_convert(self):
        if self.include_config:
            config_convertor = GatewayConfigConvertor(self._release_data, self.micro_gateway)
            self._gateway_config = config_convertor.convert()

        if self.include_stage:
            stage_convertor = StageConvertor(self._release_data, self.micro_gateway, self.publish_id)
            self._stage = stage_convertor.convert()

        if self.include_service:
            service_convertor = ServiceConvertor(self._release_data, self.micro_gateway)
            self._services = service_convertor.convert()

        if self.include_http_resource:
            # 协议类型为 http 的资源，与 grpc 等协议区分，而不是后端 proxy 类型为 http 的资源
            http_resource_convertor = HttpResourceConvertor(
                self._release_data,
                self.micro_gateway,
                self._services,
                self.publish_id,
                self.revoke_flag,
            )
            self._http_resources = http_resource_convertor.convert()

        if self.include_plugin_metadata:
            plugin_metadata_convertor = PluginMetadataConvertor(self._release_data, self.micro_gateway)
            self._plugin_metadata = plugin_metadata_convertor.convert()

    def get_kubernetes_resources(self) -> Iterable[KubernetesResource]:
        if self.include_config:
            assert self._gateway_config
            yield self._gateway_config

        if self.include_stage:
            assert self._stage
            yield self._stage

        if self.include_service:
            yield from self._services

        if self.include_http_resource:
            yield from self._http_resources

        if self.include_plugin_metadata:
            yield from self._plugin_metadata
