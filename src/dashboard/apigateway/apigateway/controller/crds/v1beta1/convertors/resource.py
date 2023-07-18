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
import datetime
import json
from typing import Any, Dict, List, Optional, Union

import pytz
from django.utils.functional import cached_property

from apigateway.controller.crds.constants import (
    ResourceRewriteHeadersStrategyEnum,
    UpstreamSchemeEnum,
    UpstreamTypeEnum,
)
from apigateway.controller.crds.release_data.release_data import ReleaseData
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor, UrlInfo
from apigateway.controller.crds.v1beta1.models.base import PluginConfig, TimeoutConfig, Upstream, UpstreamNode
from apigateway.controller.crds.v1beta1.models.gateway_resource import (
    BkGatewayResource,
    BkGatewayResourceSpec,
    ResourceRewrite,
)
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService
from apigateway.core.constants import ProxyTypeEnum
from apigateway.core.models import MicroGateway


class HttpResourceConvertor(BaseConvertor):
    def __init__(
        self,
        release_data: ReleaseData,
        micro_gateway: MicroGateway,
        gateway_service: List[BkGatewayService],
        publish_id: Union[int, None] = None,
    ):
        super().__init__(release_data, micro_gateway)
        self._gateway_services = gateway_service
        self._publish_id = publish_id

    @cached_property
    def _default_stage_service_key(self) -> str:
        # 目前环境只有一个服务
        for service in self._gateway_services:
            if service.metadata.get_label("service-type", "stage"):
                return service.metadata.name

        raise NameError("stage service not found in registry")

    def convert(self) -> List[BkGatewayResource]:
        resources: List[BkGatewayResource] = []
        for resource in self._release_data.resource_version.data:
            crd = self._convert_http_resource(resource)
            if crd:
                resources.append(crd)
        # 如果是版本发布需要加上版本路由
        if self._publish_id:
            version_route_crd = self._convert_http_resource(self._get_release_version_route_resource())
            if version_route_crd:
                resources.append(version_route_crd)
        return resources

    def _convert_http_resource(self, resource: Dict[str, Any]) -> Optional[BkGatewayResource]:
        if resource["proxy"]["type"] not in [ProxyTypeEnum.HTTP.value, ProxyTypeEnum.MOCK.value]:
            return None

        if self._release_data.stage.name in resource["disabled_stages"]:
            return None

        resource_proxy = json.loads(resource["proxy"]["config"])

        service_name = ""
        upstream = self._convert_http_resource_upstream(resource_proxy)
        # operator 会将环境级别的插件绑定到service，如果资源没有定义上游，依然绑定服务
        service_name = self._default_stage_service_key

        methods = []
        if resource["method"] != "ANY":
            methods = [resource["method"]]

        return BkGatewayResource(
            metadata=self._common_metadata(resource["name"]),
            spec=BkGatewayResourceSpec(
                name=resource["name"],
                id=resource["id"],
                description=resource["description"],
                uri=resource["path"],
                methods=methods,
                match_subpath=resource_proxy.get("match_subpath", False),
                # 此处会覆盖 upstream 定义的超时，最终以这里为准
                timeout=self._convert_http_resource_timeout(resource_proxy),
                rewrite=self._convert_http_resource_rewrite(resource_proxy),
                service=service_name,
                upstream=upstream,
                plugins=self._convert_http_resource_plugins(resource),
            ),
        )

    def _get_release_version_route_resource(self) -> dict:
        uri = "/_version"
        name = "get_release_version"
        now = datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        now_formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
        mock_result = {
            "publish_id": self._publish_id,
            "start_time": now_formatted_time,
        }
        mock_config = {
            "code": 200,
            "body": json.dumps(mock_result),
            "headers": {"Content-Type": "application/json"},
        }
        auth_config = {
            "skip_auth_verification": True,
            "auth_verified_required": False,
            "app_verified_required": False,
            "resource_perm_required": False,
        }
        resource = {
            "id": -1,
            "name": name,
            "description": "版本发布结果获取路由",
            "description_en": "version release result get route",
            "method": "GET",
            "path": uri,
            "match_subpath": False,
            "is_public": False,
            "allow_apply_permission": False,
            "proxy": {
                "type": ProxyTypeEnum.MOCK.value,
                "config": json.dumps(mock_config),
            },
            "contexts": {
                "resource_auth": {
                    "scope_type": "resource",
                    "type": "resource_auth",
                    "config": json.dumps(auth_config),
                }
            },
            "disabled_stages": [],
            "api_labels": [],
        }
        return resource

    def _convert_http_resource_upstream(self, resource_proxy: Dict[str, Any]) -> Optional[Upstream]:
        upstreams = resource_proxy.get("upstreams")
        if not upstreams:
            return None

        upstream = Upstream(
            # 因为路由中设置了超时，此处会被覆盖，加上只是作为防御
            timeout=self._convert_http_resource_timeout(resource_proxy),
            type=UpstreamTypeEnum.ROUNDROBIN,
        )

        for i in upstreams.get("hosts", []):
            url_info = UrlInfo(i["host"])
            upstream.scheme = UpstreamSchemeEnum(url_info.scheme)
            upstream.nodes.append(UpstreamNode(host=url_info.domain, port=url_info.port, weight=i.get("weight", 1)))

        return upstream

    def _convert_http_resource_timeout(self, resource_proxy: Dict[str, Any]) -> TimeoutConfig:
        # 资源没有配置则使用环境的
        timeout = resource_proxy.get("timeout") or self._release_data.stage_proxy_config.get("timeout") or 60

        return TimeoutConfig(
            connect=timeout,
            send=timeout,
            read=timeout,
        )

    def _convert_http_resource_rewrite(self, resource_proxy: Dict[str, Any]) -> ResourceRewrite:
        headers = self._convert_http_rewrite_headers(self._release_data.stage_proxy_config.get("transform_headers"))
        headers.update(self._convert_http_rewrite_headers(resource_proxy.get("transform_headers")))

        return ResourceRewrite(
            enabled=True,
            method=resource_proxy.get("method"),
            path=resource_proxy.get("path"),
            stage_headers=ResourceRewriteHeadersStrategyEnum.APPEND,
            headers=headers,
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

        if resource["proxy"]["type"] == ProxyTypeEnum.MOCK.value:
            proxy_config = json.loads(resource["proxy"]["config"])
            plugins.extend(
                [
                    PluginConfig(
                        name="bk-mock",
                        config={
                            "response_status": proxy_config["code"],
                            "response_example": proxy_config["body"],
                            "response_headers": proxy_config["headers"],
                        },
                    )
                ]
            )

        plugins.extend(
            [
                PluginConfig(name=plugin_data.name, config=plugin_data.config)
                for plugin_data in self._release_data.get_resource_plugins(resource["id"])
            ]
        )

        return plugins
