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

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .constants import (
    CheckActiveTypeEnum,
    CheckPassiveTypeEnum,
    HttpMethodEnum,
    SSLTypeEnum,
    UpstreamHashOnEnum,
    UpstreamPassHostEnum,
    UpstreamSchemeEnum,
    UpstreamTypeEnum,
)


class ApisixModel(BaseModel):
    model_config = ConfigDict(strict=True, validate_by_name=True, validate_by_alias=True)


# ------------------------------------------------------------
# been referenced models


class Labels(ApisixModel):
    # This is a dict type, so we not set the default value here
    gateway: str = Field(description="gateway")
    stage: str = Field(description="stage")


class Node(ApisixModel):
    """node for upstream"""

    host: str = Field(default="", description="host")
    port: int = Field(default=0, gt=0, description="port")
    weight: int = Field(default=1, gt=0, description="weight")

    # TODO: convert to dict({"host:port": weight})


class Timeout(ApisixModel):
    """timeout for route/upstream
    example: {"connect": 3, "send": 3, "read": 3}

    NOTE: currently there got legacy timeout 3600, so we not set the lt check here
    """

    connect: int = Field(default=60, gt=0, description="connect timeout")
    send: int = Field(default=60, gt=0, description="send timeout")
    read: int = Field(default=60, gt=0, description="read timeout")


class Plugin(ApisixModel):
    name: str = Field(description="name")
    config: Dict[str, Any] = Field(default_factory=dict, description="config")


class BaseHealthy(ApisixModel):
    http_statuses: Optional[List[int]] = Field(description="http statuses")
    successes: Optional[int] = Field(description="success count")


class PassiveHealthy(BaseHealthy):
    pass


class ActiveHealthy(BaseHealthy):
    interval: Optional[int] = Field(description="interval")


class BaseUnhealthy(ApisixModel):
    http_statuses: Optional[List[int]] = Field(description="http statuses")
    http_failures: Optional[int] = Field(description="http failures")
    tcp_failures: Optional[int] = Field(description="tcp failures")
    timeouts: Optional[int] = Field(description="timeouts")


class PassiveUnhealthy(BaseUnhealthy):
    pass


class ActiveUnhealthy(BaseUnhealthy):
    interval: Optional[int] = Field(description="interval")


class ActiveCheck(ApisixModel):
    type: CheckActiveTypeEnum = Field(default=CheckActiveTypeEnum.HTTP.value, description="type")
    timeout: Optional[int] = Field(description="timeout")
    concurrency: Optional[int] = Field(description="concurrency")
    http_path: Optional[str] = Field(description="http path")
    host: Optional[str] = Field(description="host")
    port: Optional[int] = Field(description="port")
    https_verify_certificate: Optional[bool] = Field(description="https verify certificate")
    req_headers: Optional[List[str]] = Field(description="request headers")
    healthy: Optional[ActiveHealthy] = Field(description="healthy")
    unhealthy: Optional[ActiveUnhealthy] = Field(description="unhealthy")
    # FIXME: should be one of healthy or unhealthy


class PassiveCheck(ApisixModel):
    type: CheckPassiveTypeEnum = Field(default=CheckPassiveTypeEnum.HTTP.value, description="type")
    healthy: Optional[PassiveHealthy] = Field(description="healthy")
    unhealthy: Optional[PassiveUnhealthy] = Field(description="unhealthy")


class Check(ApisixModel):
    active: Optional[ActiveCheck] = Field(default=None, description="active check")
    passive: Optional[PassiveCheck] = Field(default=None, description="passive check")

    @model_validator(mode="after")
    def check_active_or_passive(self):
        if not self.active and not self.passive:
            raise ValueError("either active or passive must be set")


class Tls(ApisixModel):
    cert: Optional[str] = Field(description="cert")
    key: Optional[str] = Field(description="key")
    client_cert_id: Optional[str] = Field(description="client cert id")

    # TODO: cert+key or client_cert_id only one is allowed


# ------------------------------------------------------------
# base models


class Upstream(ApisixModel):
    # NOTE: now we put upstream directly in service, so no name/desc; this is a struct nested in service

    # load balance
    type: UpstreamTypeEnum = Field(default=UpstreamTypeEnum.ROUNDROBIN.value, description="type")
    nodes: List[Node] = Field(default_factory=list, description="nodes")
    hash_on: Optional[UpstreamHashOnEnum] = Field(description="hash on")
    key: Optional[str] = Field(description="key")

    # health check
    checks: Optional[Check] = Field(description="checks")

    # NOTE: not support retry

    # NOTE: not support discovery_type/service_name here, we use other sd solutions

    timeout: Optional[Timeout] = Field(description="timeout")

    # NOTE: here we set to `node`; should always be `node`
    pass_host: UpstreamPassHostEnum = Field(default=UpstreamPassHostEnum.NODE.value, description="pass host")
    # NOTE: no upstream_host, This is only valid if the pass_host is set to rewrite

    # for proxy to https/grpcs upstream
    # TODO:
    tls: Optional[Tls] = Field(description="tls")


class Service(ApisixModel):
    id: str = Field(description="id", min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9-_.]+$")
    name: str = Field(description="name")
    desc: Optional[str] = Field(description="desc")
    # NOTE: we required the labels here
    labels: Labels = Field(description="labels")

    plugins: List[Plugin] = Field(default_factory=list, description="plugins")
    upstream: Upstream = Field(description="upstream")


class Route(ApisixModel):
    # NOTE: not all fields are defined here, only the fields we need

    id: str = Field(description="id", min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9-_.]+$")
    name: Optional[str] = Field(description="name")
    # NOTE: not desc for route, save memory
    # desc: Optional[str] = Field(description="desc")
    # NOTE: we required the labels here
    labels: Labels = Field(description="labels")

    scheme: UpstreamSchemeEnum = Field(default=UpstreamSchemeEnum.HTTP.value, description="scheme")

    # NOTE: use uris, not uri here, for compatibility
    uris: List[str] = Field(default_factory=list, description="uris")

    methods: List[HttpMethodEnum] = Field(default_factory=list, description="methods")
    priority: Optional[int] = Field(description="priority")
    plugins: List[Plugin] = Field(default_factory=list, description="plugins")
    # NOTE: we need the
    service_id: str = Field(description="service id")
    timeout: Optional[Timeout] = Field(description="timeout")
    enable_websocket: Optional[bool] = Field(description="enable websocket")

    # NOTE: NO upstream here
    # NOTE: NO status here


class SSLClient(ApisixModel):
    ca: Optional[str] = Field(description="ca")
    depth: Optional[int] = Field(description="depth")
    skip_mtls_uri_regex: Optional[List[str]] = Field(description="skip mtls uri regex")


class SSL(ApisixModel):
    id: str = Field(description="id", min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9-_.]+$")
    desc: Optional[str] = Field(description="desc")
    labels: Labels = Field(description="labels")
    type: str = Field(default=SSLTypeEnum.CLIENT.value, description="type")

    # TODO: support client.ca

    cert: str = Field(description="cert")
    key: str = Field(description="key")
    client: Optional[SSLClient] = Field(description="client")


class Proto(ApisixModel):
    proto: str = Field(description="proto")
    name: Optional[str] = Field(description="name")
    desc: Optional[str] = Field(description="desc")
    labels: Optional[Labels] = Field(description="labels")


class PluginMetadata(ApisixModel):
    name: str = Field(description="name")
    config: Dict[str, Any] = Field(default_factory=dict, description="config")
