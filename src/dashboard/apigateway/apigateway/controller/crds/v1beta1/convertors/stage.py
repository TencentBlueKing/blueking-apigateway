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
import base64
from typing import Dict, List, Optional, Union

from django.utils.encoding import force_bytes, force_str

from apigateway.controller.crds.base import KubernetesResourceMetadata
from apigateway.controller.crds.release_data.release_data import ReleaseData
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor, UrlInfo
from apigateway.controller.crds.v1beta1.models.base import PluginConfig
from apigateway.controller.crds.v1beta1.models.gateway_stage import BkGatewayStage, BkGatewayStageSpec, StageRewrite
from apigateway.core.micro_gateway_config import MicroGatewayHTTPInfo
from apigateway.core.models import MicroGateway


class StageConvertor(BaseConvertor):
    def __init__(self, release_data: ReleaseData, micro_gateway: MicroGateway, publish_id: Union[int, None] = None):
        super().__init__(release_data, micro_gateway)
        self._publish_id = publish_id

    def _common_metadata(self, name: str, labels: Optional[Dict[str, str]] = None) -> KubernetesResourceMetadata:
        labels = labels or {}
        if self._publish_id:
            labels["publish_id"] = str(self._publish_id)
        return super()._common_metadata(name, labels)

    def convert(self) -> BkGatewayStage:
        # FIXME: 如何处理 http/https 协议
        http_info = MicroGatewayHTTPInfo.from_micro_gateway_config(self._micro_gateway.config)
        url_info = UrlInfo(http_info.http_url)
        path_prefix = url_info.path

        plugins = self._get_default_stage_plugins()
        plugins.extend(self._get_stage_plugins())

        return BkGatewayStage(
            metadata=self._common_metadata(self._release_data.stage.name),
            spec=BkGatewayStageSpec(
                name=self._release_data.stage.name,
                description=self._release_data.stage.description,
                rewrite=StageRewrite(
                    enabled=True,
                    headers=self._convert_http_rewrite_headers(
                        self._release_data.stage_proxy_config.get("transform_headers")
                    ),
                ),
                vars=self._release_data.stage.vars,
                path_prefix=path_prefix,
                plugins=plugins,
            ),
        )

    def _get_default_stage_plugins(self) -> List[PluginConfig]:
        """Get the default plugins for stage, which is shared by all resources in the stage"""
        plugins = [
            PluginConfig(name="bk-opentelemetry"),
            PluginConfig(name="prometheus"),
            PluginConfig(name="bk-real-ip"),
            PluginConfig(name="bk-auth-validate"),
            PluginConfig(name="bk-auth-verify"),
            PluginConfig(name="bk-break-recursive-call"),
            PluginConfig(name="bk-concurrency-limit"),
            PluginConfig(name="bk-delete-sensitive"),
            PluginConfig(name="bk-log-context"),
            PluginConfig(name="bk-delete-cookie"),
            PluginConfig(name="bk-error-wrapper"),
            PluginConfig(name="bk-jwt"),
            PluginConfig(name="bk-request-id"),
            PluginConfig(name="bk-response-check"),
            PluginConfig(name="bk-permission"),
            PluginConfig(name="bk-debug"),
            PluginConfig(
                name="file-logger",
                config={
                    "path": "logs/access.log",
                },
            ),
            PluginConfig(
                name="bk-stage-context",
                config={
                    "bk_gateway_name": self._release_data.gateway.name,
                    "bk_gateway_id": self._release_data.gateway.pk,
                    "bk_stage_name": self._release_data.stage.name,
                    "jwt_private_key": force_str(base64.b64encode(force_bytes(self._release_data.jwt_private_key))),
                    "bk_api_auth": self._release_data.api_auth_config,
                },
            ),
        ]

        # Only append this plugin config if it's enabled
        #
        # TODO: Upgrade the plugin schema and remove the “enabled” field entirely,
        # it’s better to take advantage of the “_meta.disabled” field directly instead
        # of implementing our own similar mechanics.
        global_rate_limit_config = self._release_data.stage_rate_limit_config
        if global_rate_limit_config and global_rate_limit_config.get("enabled", False):
            plugins.append(PluginConfig(name="bk-global-rate-limit", config=global_rate_limit_config))

        return plugins

    def _get_stage_plugins(self):
        return [
            PluginConfig(name=plugin_data.name, config=plugin_data.config)
            for plugin_data in self._release_data.get_stage_plugins()
        ]
