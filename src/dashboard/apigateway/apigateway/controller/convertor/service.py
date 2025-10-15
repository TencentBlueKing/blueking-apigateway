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

import base64
from typing import List

from django.conf import settings
from django.utils.encoding import force_bytes, force_str

from apigateway.controller.crds.v1beta1.models.base import PluginConfig

from .base import BaseConvertor


class ServiceConvertor(BaseConvertor):
    def convert(self):
        # FIXME: merge the stage + service here
        pass

    def _build_service_plugins(self) -> List[PluginConfig]:
        plugins = self._get_stage_default_plugins()
        plugins.extend(self._get_stage_binding_plugins())
        plugins.extend(self._get_stage_extra_plugins())

        return plugins

    def _get_stage_default_plugins(self) -> List[PluginConfig]:
        """Get the default plugins for stage, which is shared by all resources in the stage"""
        default_plugins = [
            # 2024-08-19 disable the bk-opentelemetry plugin, we should let each gateway set their own opentelemetry
            # PluginConfig(name="bk-opentelemetry"),
            PluginConfig(name="prometheus"),
            PluginConfig(name="bk-real-ip"),
            PluginConfig(name="bk-auth-validate"),
            PluginConfig(name="bk-auth-verify"),
            PluginConfig(name="bk-break-recursive-call"),
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
                    "bk_api_auth": self._release_data.gateway_auth_config,
                },
            ),
        ]

        if settings.GATEWAY_CONCURRENCY_LIMIT_ENABLED:
            default_plugins.append(PluginConfig(name="bk-concurrency-limit"))

        # 多租户模式
        if settings.ENABLE_MULTI_TENANT_MODE:
            default_plugins.extend(
                [
                    PluginConfig(name="bk-tenant-verify"),
                    PluginConfig(
                        name="bk-tenant-validate",
                        config={
                            "tenant_mode": self._release_data.gateway.tenant_mode,
                            "tenant_id": self._release_data.gateway.tenant_id,
                        },
                    ),
                ]
            )
        else:
            default_plugins.append(PluginConfig(name="bk-default-tenant"))

        return default_plugins

    def _get_stage_binding_plugins(self) -> List[PluginConfig]:
        return [
            PluginConfig(name=plugin_data.name, config=plugin_data.config)
            for plugin_data in self._release_data.get_stage_plugins()
        ]

    def _get_stage_extra_plugins(self) -> List[PluginConfig]:
        gateway_name = self._release_data.gateway.name
        if gateway_name in settings.LEGACY_INVALID_PARAMS_GATEWAY_NAMES:
            return [PluginConfig(name="bk-legacy-invalid-params")]
        return []
