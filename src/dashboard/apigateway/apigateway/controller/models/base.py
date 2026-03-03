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

from typing import ClassVar, Dict, List, Optional

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

# reference to: https://github.com/apache/apisix/blob/release/3.13/apisix/schema_def.lua

# IMPORTANT RULES:
# 1. all id are string(1-64), not int, so use readable string instead of increment id
# 2. for route, don't set the desc field, save memory


# ------------------------------------------------------------
# been referenced models, use BaseApisixModel

# BaseApisixModel
#   |- Labels
#   |- Node
#   |- Timeout
#   |- Plugin
#   |- BaseHealthy
#       |- PassiveHealthy
#       |- ActiveHealthy
#   |- BaseUnhealthy
#       |- PassiveUnhealthy
#       |- ActiveUnhealthy
#   |- ActiveCheck
#   |- PassiveCheck
#   |- Check
#   |- Tls
#   |- BaseUpstream
#   |- SSLClient


class BaseApisixModel(BaseModel):
    model_config = ConfigDict(strict=True, validate_by_name=True, validate_by_alias=True)


class Labels(BaseApisixModel):
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        # Convert all values to strings
        converted_data = {key: str(value) for key, value in data.items()}
        super().__init__(**converted_data)

    def add_label(self, key: str, value: str) -> None:
        """Add a dynamic label"""
        setattr(self, key, str(value))

    def get_label(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a dynamic label"""
        return getattr(self, key, default)


class Node(BaseApisixModel):
    """node for upstream"""

    host: str = Field(min_length=1, description="host")
    port: int = Field(default=80, ge=1, le=65535, description="port")
    # the frontend make it gte 1, it's different from apisix
    weight: int = Field(default=1, gt=0, description="weight")

    # TODO: convert to dict({"host:port": weight})


class Timeout(BaseApisixModel):
    """timeout for route/upstream
    example: {"connect": 3, "send": 3, "read": 3}

    NOTE: currently there got legacy timeout 3600, so we not set the lt check here
    """

    connect: int = Field(default=60, gt=0, description="connect timeout")
    send: int = Field(default=60, gt=0, description="send timeout")
    read: int = Field(default=60, gt=0, description="read timeout")


class Plugin(BaseApisixModel):
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        super().__init__(**data)


class BaseHealthy(BaseApisixModel):
    http_statuses: Optional[List[int]] = Field(default=None, description="http statuses")
    successes: Optional[int] = Field(default=None, ge=1, le=254, description="success count")


class PassiveHealthy(BaseHealthy):
    pass


class ActiveHealthy(BaseHealthy):
    interval: Optional[int] = Field(default=None, description="interval")


class BaseUnhealthy(BaseApisixModel):
    http_statuses: Optional[List[int]] = Field(default=None, description="http statuses")
    http_failures: Optional[int] = Field(default=None, ge=1, le=254, description="http failures")
    tcp_failures: Optional[int] = Field(default=None, ge=1, le=254, description="tcp failures")
    timeouts: Optional[int] = Field(default=None, description="timeouts")


class PassiveUnhealthy(BaseUnhealthy):
    pass


class ActiveUnhealthy(BaseUnhealthy):
    interval: Optional[int] = Field(default=None, description="interval")


class ActiveCheck(BaseApisixModel):
    type: CheckActiveTypeEnum = Field(default=CheckActiveTypeEnum.HTTP, description="type")
    timeout: Optional[int] = Field(default=None, description="timeout")
    concurrency: Optional[int] = Field(default=None, description="concurrency")
    http_path: Optional[str] = Field(default=None, description="http path")
    https_verify_certificate: Optional[bool] = Field(default=None, description="https verify certificate")
    # host: Optional[str] = Field(default=None, description="host")
    # port: Optional[int] = Field(default=None, ge=1, le=65535, description="port")
    # req_headers: Optional[List[str]] = Field(default=None, description="request headers")
    healthy: Optional[ActiveHealthy] = Field(default=None, description="healthy")
    unhealthy: Optional[ActiveUnhealthy] = Field(default=None, description="unhealthy")
    # FIXME: should be one of healthy or unhealthy


class PassiveCheck(BaseApisixModel):
    type: CheckPassiveTypeEnum = Field(default=CheckPassiveTypeEnum.HTTP, description="type")
    healthy: Optional[PassiveHealthy] = Field(default=None, description="healthy")
    unhealthy: Optional[PassiveUnhealthy] = Field(default=None, description="unhealthy")


class Check(BaseApisixModel):
    active: Optional[ActiveCheck] = Field(default=None, description="active check")
    passive: Optional[PassiveCheck] = Field(default=None, description="passive check")

    @model_validator(mode="after")
    def check_active_or_passive(self):
        if not self.active and not self.passive:
            raise ValueError("either active or passive must be set")
        return self


class Tls(BaseApisixModel):
    cert: Optional[str] = Field(default=None, description="cert")
    key: Optional[str] = Field(default=None, description="key")
    client_cert_id: Optional[str] = Field(
        default=None, min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9-_.]+$", description="client cert id"
    )

    # TODO: cert+key or client_cert_id only one is allowed


class BaseUpstream(BaseApisixModel):
    # NOTE: now we put upstream directly in service, so no name/desc; this is a struct nested in service

    # load balance
    type: UpstreamTypeEnum = Field(default=UpstreamTypeEnum.ROUNDROBIN, description="type")
    nodes: List[Node] = Field(default_factory=list, description="nodes")
    hash_on: Optional[UpstreamHashOnEnum] = Field(default=None, description="hash on")
    key: Optional[str] = Field(default=None, description="key")
    scheme: Optional[UpstreamSchemeEnum] = Field(default=UpstreamSchemeEnum.HTTP, description="scheme")

    # health check
    checks: Optional[Check] = Field(default=None, description="checks")

    # NOTE: not support retry

    # NOTE: not support discovery_type/service_name here, we use other sd solutions

    timeout: Optional[Timeout] = Field(default=None, description="timeout")

    # NOTE: here we set to `node`; should always be `node`
    pass_host: UpstreamPassHostEnum = Field(default=UpstreamPassHostEnum.NODE, description="pass host")
    # NOTE: no upstream_host, This is only valid if the pass_host is set to rewrite

    # for proxy to https/grpcs upstream
    # TODO:
    tls: Optional[Tls] = Field(default=None, description="tls")


class SSLClient(BaseApisixModel):
    ca: Optional[str] = Field(default=None, min_length=128, max_length=64 * 1024, description="ca")
    depth: Optional[int] = Field(default=None, ge=0, description="depth")
    skip_mtls_uri_regex: Optional[List[str]] = Field(default=None, min_length=1, description="skip mtls uri regex")


# ------------------------------------------------------------
# base models, use ApisixModel

# ApisixModel
#   |- GatewayApisixModel
#          |- Service
#          |- Route
#          |- SSL
#          |- Proto
#   |- GlobalApisixModel
#          |- PluginMetadata


class ApisixModel(BaseModel):
    model_config = ConfigDict(strict=True, validate_by_name=True, validate_by_alias=True)

    kind: ClassVar[str]

    # NOTE: it has a id, which is string
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9-_.]+$", description="id")


# ------------------------------------------------------------
## global models, not belong to a gateway/stage


class GatewayApisixModel(ApisixModel):
    desc: Optional[str] = Field(default=None, max_length=256, description="desc")

    # NOTE: we required the labels here, bind to the gateway/stage
    labels: Labels = Field(description="labels")


class Service(GatewayApisixModel):
    kind = "service"

    name: str = Field(min_length=1, max_length=100, description="name")

    plugins: Dict[str, Plugin] = Field(default_factory=dict, description="plugins")
    upstream: BaseUpstream = Field(description="upstream")


class Route(GatewayApisixModel):
    kind = "route"
    # NOTE: not all fields are defined here, only the fields we need

    name: str = Field(min_length=1, max_length=100, description="name")

    # NOTE: use uris, not uri here, for compatibility
    uris: List[str] = Field(default_factory=list, description="uris")

    methods: List[HttpMethodEnum] = Field(default_factory=list, description="methods")
    priority: Optional[int] = Field(default=None, description="priority")
    plugins: Dict[str, Plugin] = Field(default_factory=dict, description="plugins")
    # NOTE: we need the
    service_id: Optional[str] = Field(
        default=None, min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9-_.]+$", description="service id"
    )
    timeout: Optional[Timeout] = Field(default=None, description="timeout")
    enable_websocket: Optional[bool] = Field(default=None, description="enable websocket")

    # NOTE: NO upstream here, currently we use service_id to bind the service with
    # NOTE: NO status here


class SSL(GatewayApisixModel):
    kind = "ssl"

    type: str = Field(default=SSLTypeEnum.CLIENT.value, description="type")

    cert: str = Field(min_length=128, max_length=64 * 1024, description="cert")
    key: str = Field(min_length=128, max_length=64 * 1024, description="key")
    client: Optional[SSLClient] = Field(default=None, description="client")


class Proto(GatewayApisixModel):
    kind = "proto"

    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="name")

    content: str = Field(min_length=1, max_length=1024 * 1024, description="content")


class BkRelease(GatewayApisixModel):
    kind = "_bk_release"

    publish_id: int = Field(description="publish id")
    publish_time: str = Field(description="publish time")
    apisix_version: str = Field(description="apisix version")
    resource_version: str = Field(description="resource version")


# ------------------------------------------------------------
## global models, not belong to any gateway/stage
class GlobalApisixModel(ApisixModel):
    """
    Base class for global models that do not belong to gateway.
    """

    # NOTE: we required the labels here, add apisix version label here
    labels: Labels = Field(description="labels")


class PluginMetadata(GlobalApisixModel):
    kind = "plugin_metadata"

    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        super().__init__(**data)
