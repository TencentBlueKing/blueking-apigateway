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
import json
from typing import Any, Dict, List, Optional, Union

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

    @cached_property
    def _default_stage_service_key(self) -> str:
        # 目前环境只有一个服务
        for service in self._gateway_services:
            if service.metadata.get_label("service-type", "stage"):
                return service.metadata.name

        raise NameError("stage service not found in registry")

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

    def _convert_http_resource(self, resource: Dict[str, Any]) -> Optional[BkGatewayResource]:
        if resource["proxy"]["type"] not in [ProxyTypeEnum.HTTP.value, ProxyTypeEnum.MOCK.value]:
            return None

        if self._release_data.stage.name in resource["disabled_stages"]:
            return None

        resource_proxy = json.loads(resource["proxy"]["config"])

        backend_id = resource["proxy"].get("backend_id", 0)

        service_name = ""
        upstream = self._convert_http_resource_upstream(resource_proxy, backend_id)
        # operator 会将环境级别的插件绑定到 service，如果资源没有定义上游，依然绑定服务
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

    def _get_release_version_route_resource_crd(self) -> BkGatewayResource:
        mock_config = {
            "code": 200,
            "body": json.dumps(
                {
                    "publish_id": self._publish_id,
                    "start_time": now_str(),
                }
            ),
            "headers": {"Content-Type": "application/json"},
        }
        resource = {
            "id": -1,
            "name": "apigw_builtin__mock_release_version",
            "description": "获取发布信息，用于检查版本发布结果",
            "description_en": "get release information for checking version release result",
            "method": "GET",
            "path": "/__apigw_version",
            "match_subpath": False,
            "is_public": False,
            "allow_apply_permission": False,
            "proxy": {
                "type": ProxyTypeEnum.MOCK.value,
                "config": json.dumps(mock_config),
            },
            "disabled_stages": [],
            "api_labels": [],
        }
        plugins = [
            PluginConfig(
                name="bk-mock",
                config={
                    "response_status": mock_config["code"],
                    "response_example": mock_config["body"],
                    "response_headers": mock_config["headers"],
                },
            )
        ]
        return BkGatewayResource(
            metadata=self._common_metadata(str(resource["name"])),
            spec=BkGatewayResourceSpec(
                name=resource["name"],
                id=resource["id"],
                description=resource["description"],
                uri=resource["path"],
                methods=[resource["method"]],
                match_subpath=False,
                timeout=self._convert_http_resource_timeout({"timeout": 60}),
                rewrite=ResourceRewrite(enabled=False),
                plugins=plugins,
            ),
        )

    def _convert_http_resource_upstream(self, resource_proxy: Dict[str, Any], backend_id: int) -> Optional[Upstream]:
        upstreams = self._release_data.get_resources_upstream(resource_proxy, backend_id)

        if not upstreams:
            return None

        loadbalance = self._release_data.stage_backend_config.get("loadbalance", UpstreamTypeEnum.ROUNDROBIN.value)
        hash_one = self._release_data.stage_backend_config.get("hash_on", "")
        upstream = Upstream(
            # 因为路由中设置了超时，此处会被覆盖，加上只是作为防御
            timeout=self._convert_http_resource_timeout(resource_proxy),
            type=self._convert_upstream_type(loadbalance),
            retries=self._release_data.stage_backend_config.get("retries", 0),
            retryTimeout=self._release_data.stage_backend_config.get("retry_timeout", 0),
            hash_on=self._convert_chash_hash_one_type(hash_one),
            key=self._convert_chash_hash_one_type_key(
                hash_one, self._release_data.stage_backend_config.get("key", "")
            ),
        )

        for host in upstreams.get("hosts", []):
            url_info = UrlInfo(self._release_data.get_upstream_host(host))
            upstream.scheme = UpstreamSchemeEnum(url_info.scheme)
            upstream.nodes.append(UpstreamNode(host=url_info.domain, port=url_info.port, weight=host.get("weight", 1)))

        return upstream

    def _convert_http_resource_timeout(self, resource_proxy: Dict[str, Any]) -> TimeoutConfig:
        # 资源没有配置则使用环境的, 兼容 v1/v2 数据
        resource_timeout = self._convert_timeout(resource_proxy.get("timeout", 0))
        stage_timeout = self._convert_timeout(self._release_data.stage_backend_config.get("timeout", 0))

        return TimeoutConfig(
            connect=resource_timeout["connect"] or stage_timeout["connect"] or 60,
            send=resource_timeout["send"] or stage_timeout["send"] or 60,
            read=resource_timeout["read"] or stage_timeout["read"] or 60,
        )

    def _convert_http_resource_rewrite(self, resource_proxy: Dict[str, Any]) -> ResourceRewrite:
        if self._release_data.resource_version.is_schema_v2:
            # stage_headers及headers相关处理在operator处理
            return ResourceRewrite(
                enabled=True,
                method=resource_proxy.get("method"),
                path=resource_proxy.get("path"),
            )

        headers = self._convert_http_rewrite_headers(self._release_data.stage_backend_config.get("transform_headers"))
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
