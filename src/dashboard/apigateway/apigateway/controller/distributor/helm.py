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
import os
import tempfile
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple, Type

from blue_krill.cubing_case import shortcuts
from django.conf import settings
from packaging.version import parse as parse_version
from pydantic import BaseModel, Field, PrivateAttr

from apigateway.controller.crds.v1beta1.convertor import CustomResourceConvertor
from apigateway.controller.crds.v1beta1.models.base import GatewayCustomResource
from apigateway.controller.crds.v1beta1.models.gateway_config import BkGatewayConfig, BkGatewayConfigSpec
from apigateway.controller.crds.v1beta1.models.gateway_plugin_metadata import (
    BkGatewayPluginMetadata,
    BkGatewayPluginMetadataSpec,
)
from apigateway.controller.crds.v1beta1.models.gateway_resource import BkGatewayResource, BkGatewayResourceSpec
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService, BkGatewayServiceSpec
from apigateway.controller.crds.v1beta1.models.gateway_stage import BkGatewayStage, BkGatewayStageSpec
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.helm.chart import ChartHelper
from apigateway.controller.helm.generator import CrdChartGenerator
from apigateway.controller.helm.release import ReleaseHelper, ReleaseInfo
from apigateway.controller.micro_gateway_config import MicroGatewayBcsInfo
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.controller.registry.base import Registry
from apigateway.controller.registry.dict import DictRegistry
from apigateway.core.models import MicroGateway, Release, ResourceVersion

logger = logging.getLogger(__name__)


class HelmReleaseContext(BaseModel):
    chart_name: str = Field(default="")
    chart_version: str = Field(default="")
    app_version: str = Field(default="")

    config: Optional[BkGatewayConfigSpec]
    _raw_config: Optional[BkGatewayConfigSpec] = PrivateAttr()

    stage: Optional[BkGatewayStageSpec]
    _raw_stage: Optional[BkGatewayStageSpec] = PrivateAttr()

    services: Dict[str, BkGatewayServiceSpec] = Field(default_factory=OrderedDict)
    _raw_services: Dict[str, BkGatewayServiceSpec] = PrivateAttr(default_factory=OrderedDict)

    resources: Dict[str, BkGatewayResourceSpec] = Field(default_factory=OrderedDict)
    _raw_resources: Dict[str, BkGatewayResourceSpec] = PrivateAttr(default_factory=OrderedDict)

    plugin_metadata: Dict[str, BkGatewayPluginMetadataSpec] = Field(default_factory=OrderedDict)
    _raw_plugin_metadata: Dict[str, BkGatewayPluginMetadataSpec] = PrivateAttr(default_factory=OrderedDict)

    @property
    def raw_config(self):
        return self._raw_config

    @property
    def raw_stage(self):
        return self._raw_stage

    @property
    def raw_services(self):
        return self._raw_services

    @property
    def raw_resources(self):
        return self._raw_resources

    @property
    def raw_plugin_metadata(self):
        return self._raw_plugin_metadata

    def _restore_groups(
        self,
        registry: Registry,
        resource_type: Type[GatewayCustomResource],
        raw_groups: Dict[str, Any],
        spec_groups: Dict[str, Any],
    ):
        for resource in registry.iter_by_type(resource_type):
            raw_groups[resource.name] = resource
            spec_groups[resource.name] = getattr(resource, "spec", None)

    def _restore_single(self, registry: Registry, resource_type: Type[GatewayCustomResource]):
        for resource in registry.iter_by_type(resource_type):
            return resource, getattr(resource, "spec", None)

        return None, None

    def restore(self, registry: Registry):
        """通过 Registry 恢复结构"""
        self._raw_config, self.config = self._restore_single(registry, BkGatewayConfig)  # type: ignore
        self._raw_stage, self.stage = self._restore_single(registry, BkGatewayStage)  # type: ignore
        self._restore_groups(registry, BkGatewayPluginMetadata, self._raw_plugin_metadata, self.plugin_metadata)
        self._restore_groups(registry, BkGatewayService, self._raw_services, self.services)
        self._restore_groups(registry, BkGatewayResource, self._raw_resources, self.resources)

        return self

    def renew_version(self, resource_version: ResourceVersion):
        """更新版本"""

        self.app_version = resource_version.version
        parsed_version = parse_version(self.app_version)

        self.chart_version = f"{parsed_version.public}+{int(time.time())}"


class HelmDistributor(BaseDistributor):
    def __init__(
        self,
        operator: str = "",
        chart_helper: Optional[ChartHelper] = None,
        release_helper: Optional[ReleaseHelper] = None,
        generate_chart: bool = True,
        release_callback: Optional[Callable[[Release, MicroGateway, ReleaseInfo], bool]] = None,
    ):
        if not operator:
            self.operator = getattr(settings, "BK_APP_CODE", "")

        self.operator = operator
        self.chart_helper = chart_helper or ChartHelper()
        self.release_helper = release_helper or ReleaseHelper()
        self.generate_chart = generate_chart
        self.release_callback = release_callback

    def _convert_release_context(
        self,
        release: Release,
        micro_gateway: MicroGateway,
    ) -> HelmReleaseContext:
        convertor = CustomResourceConvertor(
            release=release,
            micro_gateway=micro_gateway,
            include_config=False,  # BkGatewayConfig 随着 micro-gateway 的 release 下发，所以无需包含
            include_plugin_metadata=True,
            publish_id=None,
        )
        convertor.convert()

        registry = DictRegistry()
        registry.sync_resources_by_key_prefix(convertor.get_kubernetes_resources())

        # 将目标 registry 转换成适合 helm 生成的结构
        return HelmReleaseContext(
            chart_name=shortcuts.to_lower_dash_case(f"bkapi-release-{release.gateway.name}-{release.stage.name}"),
            chart_version=release.resource_version.version or "0.0.0-auto",
        ).restore(registry)

    def _distribute_chart(
        self,
        procedure_logger: ReleaseProcedureLogger,
        project_name: str,
        generator: CrdChartGenerator,
    ):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with procedure_logger.step("generate chart"):
                chart_path = generator.generate(tmp_dir)

            with procedure_logger.step("push chart"):
                repo_info = self.chart_helper.get_project_repo_info(project_name)
                self.chart_helper.push_chart(chart_path, repo_info)

    def distribute(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """将 release 通过 bcs helm manager 发布"""
        bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(micro_gateway.config)
        context: HelmReleaseContext = self._convert_release_context(release, micro_gateway)
        template_dir = os.path.join(settings.BASE_DIR, "templates", "controller", "v1beta1", "crd-chart")
        generator = CrdChartGenerator(template_dir=template_dir, context=context)
        procedure_logger = ReleaseProcedureLogger(
            "edge-gateway-releasing",
            logger=logger,
            gateway=release.gateway,
            stage=release.stage,
            micro_gateway=micro_gateway,
            release_task_id=release_task_id,
        )

        # TODO 在不需要重新生成的时候复用原有的 chart
        if self.generate_chart:
            # 为了避免覆盖 chart，需要升级 chart 版本
            # context.renew_version(release.resource_version)
            # 生成并推送新的 chart 到指定的项目仓库中
            self._distribute_chart(
                generator=generator, procedure_logger=procedure_logger, project_name=bcs_info.project_name
            )

        values = generator.generate_values()

        with procedure_logger.step("chart-deploying"):
            # 发布
            found, result = self.release_helper.ensure_release(
                chart_name=context.chart_name,
                chart_version=context.chart_version,
                release_name=f"{context.chart_name}-release",
                values=values,
                namespace=bcs_info.namespace,
                cluster_id=bcs_info.cluster_id,
                project_id=bcs_info.project_name,
                repository=bcs_info.project_name,
                operator=self.operator,
            )
            if not found:
                return (
                    False,
                    f"release chart[chart_name:{context.chart_name},chart_version:{context.chart_version}]  not found ",
                )

        return True, ""

    def revoke(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """卸载对应的 helm release"""
        # TODO: Implement me
        return False, ""
