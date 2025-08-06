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
import json
from typing import Any, Dict, List, Optional, Union

from apigateway.controller.crds.release_data.release_data import ReleaseData
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor
from apigateway.controller.crds.v1beta1.models.base import PluginConfig, TimeoutConfig
from apigateway.controller.crds.v1beta1.models.gateway_resource import (
    BkGatewayResource,
    BkGatewayResourceSpec,
    ResourceRewrite,
)
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService
from apigateway.core.constants import ProxyTypeEnum
from apigateway.core.models import MicroGateway
from apigateway.utils.time import now_str


class HttpResourceConvertor(BaseConvertor):
    def __init__(
        self,
        release_data: ReleaseData,
        micro_gateway: MicroGateway,
        gateway_service: List[BkGatewayService],
        publish_id: Union[int, None] = None,
        revoke_flag: Union[bool, None] = False,
    ):
        super().__init__(release_data, micro_gateway)
        self._gateway_services = gateway_service
        self._publish_id = publish_id
        self._revoke_flag = revoke_flag

    def convert(self) -> List[BkGatewayResource]:
        resources: List[BkGatewayResource] = []
        if not self._revoke_flag:
            for resource in self._release_data.resource_version.data:
                crd = self._convert_http_resource(resource)
                if crd:
                    resources.append(crd)
        # 如果是版本发布需要加上版本路由，版本发布需要新增一个版本路由，方便查询发布结果探测
        if self._publish_id:
            resources.append(self._get_release_version_route_resource_crd())

        return resources

    # TODO: speed up
    def _stage_backend_service_name(self, backend_id: int) -> str:
        # 目前环境只有一个服务
        for service in self._gateway_services:
            if service.metadata.get_label("backend-id") == str(backend_id):
                return service.metadata.name

        raise NameError("stage service not found in registry")

    def _convert_http_resource(self, resource: Dict[str, Any]) -> Optional[BkGatewayResource]:
        if resource["proxy"]["type"] not in [ProxyTypeEnum.HTTP.value]:
            return None

        # TODO: should remove disabled_stages in the future
        if self._release_data.stage.name in resource["disabled_stages"]:
            return None

        resource_proxy = json.loads(resource["proxy"]["config"])
        backend_id = resource["proxy"].get("backend_id", 0)

        # operator 会将环境级别的插件绑定到 service，如果资源没有定义上游，依然绑定服务
        methods = []
        if resource["method"] != "ANY":
            methods = [resource["method"]]

        spec = BkGatewayResourceSpec(
            id=resource["id"],
            name=resource["name"],
            description=resource["description"],
            uri=resource["path"],
            methods=methods,
            match_subpath=resource_proxy.get("match_subpath", False),
            enable_websocket=resource.get("enable_websocket", False),
            # 此处会覆盖 upstream 定义的超时，最终以这里为准
            rewrite=self._convert_http_resource_rewrite(resource_proxy),
            service=self._stage_backend_service_name(backend_id),
            plugins=self._convert_http_resource_plugins(resource),
            # NOTE: should set to None here !!!!!!!
            # NOTE: dangerous, keep this line here, otherwise would generate an empty upstream for route
            # NOTE: will make all the routes wrong!
            upstream=None,
        )

        # NOTE: should check it's none here
        if spec.upstream is not None:
            raise ValueError(
                "spec.upstream must be None at this point. "
                "This is dangerous: keeping this check is critical, otherwise an empty upstream would be generated for the route, "
                "which will make all the routes wrong!"
            )

        # only set the timeout if the resource has timeout
        # NOTE: it's different with the previous version
        timeout = self._convert_http_resource_timeout(resource_proxy)
        if timeout:
            spec.timeout = timeout

        return BkGatewayResource(
            metadata=self._common_metadata(resource["name"]),
            spec=spec,
        )

    def _get_release_version_route_resource_crd(self) -> BkGatewayResource:
        plugins = [
            PluginConfig(
                name="bk-mock",
                config={
                    "response_status": 200,
                    "response_example": json.dumps(
                        {
                            "publish_id": self._publish_id,
                            "start_time": now_str(),
                        }
                    ),
                    "response_headers": {"Content-Type": "application/json"},
                },
            )
        ]

        resource_name = "apigw_builtin__mock_release_version"
        return BkGatewayResource(
            metadata=self._common_metadata(resource_name),
            spec=BkGatewayResourceSpec(
                id=-1,
                name=resource_name,
                description="获取发布信息，用于检查版本发布结果",
                uri="/__apigw_version",
                methods=["GET"],
                match_subpath=False,
                enable_websocket=False,
                timeout=self._convert_http_resource_timeout({"timeout": 60}),
                rewrite=ResourceRewrite(enabled=False),
                plugins=plugins,
            ),
        )

    def _convert_http_resource_timeout(self, resource_proxy: Dict[str, Any]) -> Optional[TimeoutConfig]:
        # FIXME: it not works here, should check
        # 资源如果没有配置，则没有，默认使用关联 service 的 timeout
        timeout = resource_proxy.get("timeout")
        if not timeout:
            return None

        return TimeoutConfig(
            connect=timeout,
            send=timeout,
            read=timeout,
        )

    def _convert_http_resource_rewrite(self, resource_proxy: Dict[str, Any]) -> ResourceRewrite:
        return ResourceRewrite(
            enabled=True,
            method=resource_proxy.get("method"),
            path=resource_proxy.get("path"),
        )

    def _convert_http_resource_plugins(self, resource: Dict[str, Any]) -> List[PluginConfig]:
        resource_auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])

        plugins = [
            PluginConfig(
                name="bk-resource-context",
                config={
                    "bk_resource_id": resource["id"],
                    "bk_resource_name": resource["name"],
                    "bk_resource_auth": {
                        "verified_app_required": resource_auth_config.get("app_verified_required", True),
                        "verified_user_required": resource_auth_config.get("auth_verified_required", True),
                        "resource_perm_required": resource_auth_config.get("resource_perm_required", True),
                        "skip_user_verification": resource_auth_config.get("skip_auth_verification", False),
                    },
                },
            ),
        ]

        plugins.extend(
            [
                PluginConfig(name=plugin_data.name, config=plugin_data.config)
                for plugin_data in self._release_data.get_resource_plugins(resource["id"])
            ]
        )

        return plugins
