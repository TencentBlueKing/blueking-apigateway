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

from apigateway.controller.convertor import (
    ProtoConvertor,
    RouteConvertor,
    ServiceConvertor,
    SSLConvertor,
)
from apigateway.controller.models.base import ApisixModel
from apigateway.controller.release_data import ReleaseData
from apigateway.core.models import Release

logger = logging.getLogger(__name__)


class GlobalApisixResourceConvertor:
    """全局资源转换器"""

    # FIXME: convert plugin_metadata

    def convert(self):
        return NotImplementedError()


@dataclass
class GatewayApisixResourceConvertor:
    """网关资源转换器"""

    # 为何 Convertor 需要一个中间的 registry？
    # 1. registry 抽象可以让 Convertor 不耦合任何具体类型
    # 2. 转换过程中可以通过 registry 来查询确保引用正确（如 BkgatewayResource.service 字段）

    # 那为何使用中间 registry 而不是最终目标的 registry？
    # 1. 转换过程会持续写入到 registry 中，中途如果遇到数据异常会中断，不保证原子性
    # 2. 转换过程也会从 registry 查询，如果使用目标 registry，会有历史数据的干扰
    # 3. 中间 registry 应该看做目标 registry 的最终状态

    release: Release
    publish_id: Optional[int] = field(default=None)

    # micro_gateway: MicroGateway
    # 是否是撤销资源
    revoke_flag: Optional[bool] = field(default=False)
    # 包含哪些资源的开关
    # include_config: bool = field(default=True)
    # include_plugin_metadata: bool = field(default=True)
    # 默认包含 stage 资源，调用方不需要传

    # include_stage: bool = field(default=True)
    # include_http_resource: bool = field(default=True)
    # include_service: bool = field(default=True)

    # 转换后的资源
    # _gateway_config: Optional[BkGatewayConfig] = field(init=False, default=None)
    # _stage: Optional[BkGatewayStage] = field(init=False, default=None)

    _converted_services: List[ApisixModel] = field(init=False, default_factory=list)
    _converted_routes: List[ApisixModel] = field(init=False, default_factory=list)
    _converted_ssls: List[ApisixModel] = field(init=False, default_factory=list)
    _converted_protos: List[ApisixModel] = field(init=False, default_factory=list)

    # _plugin_metadata: List[BkGatewayPluginMetadata] = field(init=False, default_factory=list)

    def __post_init__(self):
        if self.release.resource_version.is_schema_v2:
            self._release_data = ReleaseData(self.release)
        else:
            raise ValueError("Only support resource_version schema v2, v1 is deprecated")

    def convert(self):
        # config_convertor = GatewayConfigConvertor(self._release_data, self.micro_gateway)
        # self._gateway_config = config_convertor.convert()

        # stage_convertor = StageConvertor(self._release_data, self.micro_gateway, self.publish_id)
        # self._stage = stage_convertor.convert()

        service_convertor = ServiceConvertor(self._release_data, self.publish_id)
        self._converted_services = service_convertor.convert()

        # FIXME: build the mapping
        backend_service_mapping = {}

        # 协议类型为 http 的资源，与 grpc 等协议区分，而不是后端 proxy 类型为 http 的资源
        route_convertor = RouteConvertor(
            self._release_data,
            backend_service_mapping,
            self.publish_id,
            self.revoke_flag,
        )
        self._converted_routes = route_convertor.convert()

        ssl_convertor = SSLConvertor(self._release_data)
        self._converted_ssls = ssl_convertor.convert()

        proto_convertor = ProtoConvertor(self._release_data)
        self._converted_protos = proto_convertor.convert()

        # if self.include_plugin_metadata:
        #     plugin_metadata_convertor = PluginMetadataConvertor(self._release_data, self.micro_gateway)
        #     self._plugin_metadata = plugin_metadata_convertor.convert()

    def get_apisix_resources(self) -> Iterable[ApisixModel]:
        yield from self._converted_ssls

        yield from self._converted_protos

        yield from self._converted_services

        yield from self._converted_routes

        # if self.include_plugin_metadata:
        #     yield from self._plugin_metadata
