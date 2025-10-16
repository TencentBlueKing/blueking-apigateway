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

from apigateway.controller.models.base import Plugin, Route, Timeout
from apigateway.controller.release_data import ReleaseData
from apigateway.controller.uri_render import UpstreamURIRender, URIRender
from apigateway.core.constants import ProxyTypeEnum
from apigateway.utils.time import now_str

from .base import BaseConvertor

SUBPATH_PARAM_NAME = "bk_api_subpath_match_param_name"


class RouteConvertor(BaseConvertor):
    def __init__(
        self,
        release_data: ReleaseData,
        backend_service_mapping: Dict[int, str],
        publish_id: Union[int, None] = None,
        revoke_flag: Union[bool, None] = False,
    ):
        super().__init__(release_data)
        self._publish_id = publish_id
        self._revoke_flag = revoke_flag
        self._backend_service_mapping = backend_service_mapping

    def _get_service_id(self, backend_id: int) -> str:
        service_id = self._backend_service_mapping.get(backend_id)
        if not service_id:
            raise NameError("stage service not found in registry")
        return service_id

    def convert(self) -> List[Route]:
        routes: List[Route] = []

        if not self._revoke_flag:
            for resource in self._release_data.resource_version.data:
                route = self._convert_http_route(resource)
                if route:
                    routes.append(route)
        # 如果是版本发布需要加上版本路由，版本发布需要新增一个版本路由，方便查询发布结果探测
        if self._publish_id:
            routes.append(self._get_release_version_detect_route())

        return routes

    def _convert_http_route(self, resource: Dict[str, Any]) -> Optional[Route]:
        if resource["proxy"]["type"] not in [ProxyTypeEnum.HTTP.value]:
            return None

        # TODO: should remove disabled_stages in the future
        if self._release_data.stage.name in resource["disabled_stages"]:
            return None

        resource_proxy = json.loads(resource["proxy"]["config"])
        backend_id = resource["proxy"].get("backend_id", 0)

        if backend_id == 0:
            raise ValueError(f"backend_id is 0 or not set, which is not allowed. resource: {resource}")

        # operator 会将环境级别的插件绑定到 service，如果资源没有定义上游，依然绑定服务
        methods = []
        if resource["method"] != "ANY":
            methods = [resource["method"]]

        match_subpath = resource_proxy.get("match_subpath", False)

        plugins = self._convert_http_resource_plugins(resource, resource_proxy)

        route = Route(
            # FIXME: add labels
            # example: bk-esb.prod.996
            id=resource["id"],
            # example: bk-esb-prod-data-v3-aiops-get-aiops-sampleset-list
            # FIXME: the resource_name max length is 256, while the apisix name max length is 100
            name=resource["name"],
            # NOTE: no desc for route, save memory
            # desc=resource["description"],
            uris=self._convert_uris(
                path=resource["path"],
                match_subpath=match_subpath,
            ),
            methods=methods,
            plugins=plugins,
            service_id=self._get_service_id(backend_id),
            enable_websocket=resource.get("enable_websocket", False),
            # NOTE: should not set upstream here!
        )

        # only set the timeout if the resource has timeout
        # 此处会覆盖 upstream 定义的超时，最终以这里为准
        timeout = self._convert_route_timeout(resource_proxy)
        if timeout:
            route.timeout = timeout

        return route

    def _convert_uris(self, path: str, match_subpath: bool) -> List[str]:
        gateway_name = self._release_data.gateway.name
        stage_name = self._release_data.stage.name

        uri = f"/api/{gateway_name}/{stage_name}/" + path.lstrip("/")
        uri_without_suffix_slash = uri.rstrip("/")

        rendered_uri_without_suffix_slash = URIRender().render(uri_without_suffix_slash, self._release_data.stage.vars)
        if match_subpath:
            return [
                rendered_uri_without_suffix_slash,
                rendered_uri_without_suffix_slash + "/*" + SUBPATH_PARAM_NAME,
            ]

        # no match_subpath
        if "/:" in rendered_uri_without_suffix_slash:
            return [
                rendered_uri_without_suffix_slash,
                rendered_uri_without_suffix_slash + "/",
            ]

        return [rendered_uri_without_suffix_slash + "/?"]

    def _convert_route_timeout(self, resource_proxy: Dict[str, Any]) -> Optional[Timeout]:
        # 资源如果没有配置，则没有，默认使用关联 service 的 timeout
        timeout = resource_proxy.get("timeout")
        if not timeout:
            return None

        return Timeout(
            connect=timeout,
            send=timeout,
            read=timeout,
        )

    def _convert_http_resource_plugins(self, resource: Dict[str, Any], resource_proxy: Dict[str, Any]) -> List[Plugin]:
        resource_auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])

        plugins = [
            Plugin(
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
            # TODO: check the bk-proxy-rewrite plugin gen in operator
            Plugin(
                name="bk-proxy-rewrite",
                config=self._build_bk_proxy_rewrite_config(resource_proxy),
            ),
        ]

        plugins.extend(
            [
                Plugin(name=plugin_data.name, config=plugin_data.config)
                for plugin_data in self._release_data.get_resource_plugins(resource["id"])
            ]
        )

        return plugins

    def _build_bk_proxy_rewrite_config(self, resource_proxy: Dict[str, Any]) -> Dict[str, Any]:
        # dashboard only make method+path here
        path = resource_proxy.get("path")
        method = resource_proxy.get("method")
        match_subpath = resource_proxy.get("match_subpath", False)

        config: Dict[str, Any] = {}
        if path:
            upstream_uri = UpstreamURIRender().render(path, self._release_data.stage.vars)
            if match_subpath:
                config["match_subpath"] = True
                # FIXME: make it const
                config["subpath_param_name"] = SUBPATH_PARAM_NAME
                # "%s/${%s}"
                config["uri"] = upstream_uri.rstrip("/") + "/${" + SUBPATH_PARAM_NAME + "}"
            else:
                config["uri"] = upstream_uri

        if method and method != "ANY":
            config["method"] = method

        return config

    def _get_release_version_detect_route(self) -> Route:
        plugins = [
            Plugin(
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

        stage_name = self._release_data.stage.name
        gateway_name = self._release_data.gateway.name
        return Route(
            # FIXME: add labels
            id=f"{gateway_name}.{stage_name}.-1",
            # example: bk-apigateway-prod-apigw-builtin-mock-release-version
            name=f"{gateway_name}-{stage_name}-builtin-mock-release-version",
            desc="route for detect release version",
            # example:/api/bk-apigateway/prod/__apigw_version
            uris=[f"/api/{gateway_name}/{stage_name}/__apigw_version"],
            methods=["GET"],
            enable_websocket=False,
            timeout=Timeout(connect=60, send=60, read=60),
            plugins=plugins,
        )
