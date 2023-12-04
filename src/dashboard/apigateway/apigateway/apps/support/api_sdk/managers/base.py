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
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Type

from apigateway.apps.support.api_sdk.exceptions import DistributeError, ResourcesIsEmpty
from apigateway.apps.support.api_sdk.models import (
    DistributeResult,
    Distributor,
    Generator,
    Packager,
    SDKContext,
    SDKManager,
)
from apigateway.core.constants import HTTP_METHOD_ANY
from apigateway.core.models import ResourceVersion

logger = logging.getLogger(__name__)


@dataclass
class BaseSDKManager(SDKManager):
    include_private_resources: bool = False
    is_public: bool = False
    version: str = ""

    # 生成器类
    generator_cls: ClassVar[Optional[Type[Generator]]] = None
    # 打包器类
    packager_cls: ClassVar[Optional[Type[Packager]]] = None
    # 公共发布器类
    public_distributor_cls: ClassVar[Optional[Type[Distributor]]] = None
    # 私有发布器类
    private_distributor_cls: ClassVar[Optional[Type[Distributor]]] = None

    def get_resources(self, context: SDKContext) -> List[Dict[str, Any]]:
        resources = []
        for resource in context.resource_version.data:
            if not self._should_included_to_sdk(resource):
                continue

            resources.append(resource)

        return resources

    def _should_included_to_sdk(self, resource) -> bool:
        """资源是否应该被包含到 SDK"""
        if resource["method"] == HTTP_METHOD_ANY:
            return False

        return True

    def get_generator(self, context: SDKContext, **kwargs) -> Generator:
        """获取生成器对象"""
        if not self.generator_cls:
            raise TypeError("generator_cls is required")

        return self.generator_cls(context=context, **kwargs)

    def get_packager(self, context: SDKContext, **kwargs) -> Packager:
        """获取打包器对象"""
        if not self.packager_cls:
            raise TypeError("packager_cls is required")

        return self.packager_cls(context=context, **kwargs)

    def get_public_distributor(self, context: SDKContext, **kwargs) -> Distributor:
        """获取公共发布器对象"""
        if not self.public_distributor_cls:
            raise TypeError("distributor_cls is required")

        return self.public_distributor_cls(context=context, **kwargs)

    def get_private_distributor(self, context: SDKContext, **kwargs) -> Optional[Distributor]:
        """获取私有发布器对象"""
        if self.private_distributor_cls:
            return self.private_distributor_cls(context=context, **kwargs)

        return None

    def get_distributor(self, context: SDKContext, **kwargs) -> Optional[Distributor]:
        """获取发布器对象"""

        if context.is_public:
            return self.get_public_distributor(context=context, **kwargs)

        return self.get_private_distributor(context=context, **kwargs)

    def get_context(self, resource_version: ResourceVersion) -> SDKContext:
        raise NotImplementedError

    def update_context(
        self,
        context: SDKContext,
        files: List[str],
        distribute_result: Optional[DistributeResult],
    ):
        if distribute_result:
            context.url = distribute_result.url

    def _distribute(
        self,
        context: SDKContext,
        output_dir: str,
        files: List[str],
    ):
        distributor = self.get_distributor(context)
        if not distributor:
            return

        distribute_result = None
        try:
            distribute_result = distributor.distribute(output_dir, files)
        except DistributeError as err:
            if not context.is_public:
                logger.warning("distribute sdk by private distributor %s failed, skipped, %s", distributor.name, err)
            else:
                raise

        if not distribute_result:
            return

        if context.is_public:
            context.is_distributed = True

        self.update_context(context, files, distribute_result)

    def handle(self, output_dir: str, resource_version: ResourceVersion) -> SDKContext:
        context = self.get_context(resource_version)

        resources = self.get_resources(context)
        if not resources:
            raise ResourcesIsEmpty()

        generator = self.get_generator(context)
        packager = self.get_packager(context)

        generator.generate(output_dir, resources)
        files = packager.pack(output_dir)
        context.files = files

        self._distribute(context, output_dir, files)
        return context
