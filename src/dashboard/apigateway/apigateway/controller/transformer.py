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
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from apigateway.controller.convertor import (
    BkReleaseConvertor,
    RouteConvertor,
    ServiceConvertor,
)
from apigateway.controller.convertor.constants import LABEL_KEY_BACKEND_ID
from apigateway.controller.convertor.plugin_metadata import PluginMetadataConvertor
from apigateway.controller.models import ApisixModel, GatewayApisixModel
from apigateway.controller.release_data import ReleaseData
from apigateway.core.models import Release

logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    @abstractmethod
    def transform(self):
        raise NotImplementedError()

    @abstractmethod
    def get_transformed_resources(self) -> Iterable[ApisixModel]:
        raise NotImplementedError()


class GlobalApisixResourceTransformer(BaseTransformer):
    """全局资源转换器"""

    def __init__(self):
        self._converted_plugin_metadata: List[ApisixModel] = []

    def transform(self):
        plugin_metadata_convertor = PluginMetadataConvertor()
        self._converted_plugin_metadata = plugin_metadata_convertor.convert()

    def get_transformed_resources(self) -> Iterable[ApisixModel]:
        yield from self._converted_plugin_metadata


class GatewayApisixResourceTransformer(BaseTransformer):
    """网关资源转换器"""

    # 为何 Convertor 需要一个中间的 registry？
    # 1. registry 抽象可以让 Convertor 不耦合任何具体类型
    # 2. 转换过程中可以通过 registry 来查询确保引用正确

    # 那为何使用中间 registry 而不是最终目标的 registry？
    # 1. 转换过程会持续写入到 registry 中，中途如果遇到数据异常会中断，不保证原子性
    # 2. 转换过程也会从 registry 查询，如果使用目标 registry，会有历史数据的干扰
    # 3. 中间 registry 应该看做目标 registry 的最终状态

    def __init__(self, release: Release, publish_id: Optional[int] = None, revoke_flag: Optional[bool] = False):
        if release.resource_version.is_schema_v2:
            self._release_data = ReleaseData(release)
        else:
            raise ValueError("Only support resource_version schema v2, v1 is deprecated")

        self.publish_id = publish_id
        # 是否是撤销资源
        self.revoke_flag = revoke_flag

        # 转换后的资源
        self._converted_services: List[GatewayApisixModel] = []
        self._converted_routes: List[GatewayApisixModel] = []
        self._converted_ssls: List[GatewayApisixModel] = []
        self._converted_protos: List[GatewayApisixModel] = []
        self._converted_bk_releases: List[GatewayApisixModel] = []

    def transform(self):
        # FIXME:
        # 1. should check the proto_id of route plugins are all exists
        # 2. should check the ssl_id of service.upstream are all exists
        # 3. distribute the ssl/proto

        service_convertor = ServiceConvertor(self._release_data, self.publish_id)
        self._converted_services = service_convertor.convert()

        backend_service_mapping: Dict[int, str] = {}
        for svc in self._converted_services:
            backend_id = svc.labels.get_label(LABEL_KEY_BACKEND_ID)
            if backend_id:
                # the label value type is string, so we need to convert it to int
                backend_service_mapping[int(backend_id)] = svc.id

        logger.debug("the mapping: %s", backend_service_mapping)

        # 协议类型为 http 的资源，与 grpc 等协议区分，而不是后端 proxy 类型为 http 的资源
        route_convertor = RouteConvertor(
            self._release_data,
            backend_service_mapping,
            self.publish_id,
            self.revoke_flag,
        )
        self._converted_routes = route_convertor.convert()

        # FIXME: impl it
        # ssl_convertor = SSLConvertor(self._release_data)
        # self._converted_ssls = ssl_convertor.convert()

        # FIXME: impl it
        # proto_convertor = ProtoConvertor(self._release_data)
        # self._converted_protos = proto_convertor.convert()

        bk_release_convertor = BkReleaseConvertor(self._release_data, self.publish_id)
        self._converted_bk_releases = bk_release_convertor.convert()

    def get_transformed_resources(self) -> Iterable[ApisixModel]:
        yield from self._converted_ssls

        yield from self._converted_protos

        yield from self._converted_services

        yield from self._converted_routes

        # NOTE: this should be the last resource
        yield from self._converted_bk_releases
