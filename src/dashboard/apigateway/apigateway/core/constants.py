# -*- coding: utf-8 -*-
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
import re
from enum import Enum

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _


class GatewayStatusEnum(StructuredEnum):
    INACTIVE = EnumField(0, "已停用")
    ACTIVE = EnumField(1, "启用中")


# TODO: delete it in 1.14
class APIHostingTypeEnum(StructuredEnum):
    """网关托管类型，影响特性集"""

    DEFAULT = EnumField(0, "apigateway-ng")
    MICRO = EnumField(1, _("微网关"))


class MicroGatewayStatusEnum(StructuredEnum):
    """微网关实例状态"""

    PENDING = EnumField("pending", _("待安装"))
    INSTALLING = EnumField("installing", _("安装中"))
    INSTALLED = EnumField("installed", _("已安装"))
    UPDATED = EnumField("updated", _("已更新"))
    # 可能会因为 helm install 超时导致失败，此时资源可能更新了，但 release 状态未更新
    # 所以不能简单标识安装或者未安装
    ABNORMAL = EnumField("abnormal", _("安装异常"))


class BackendUpstreamTypeEnum(StructuredEnum):
    """后端 upstream 类型"""

    NODE = EnumField("node", _("节点"))
    SERVICE_DISCOVERY = EnumField("service_discovery", _("服务发现"))


class BackendConfigTypeEnum(StructuredEnum):
    """资源 Proxy 配置类型"""

    DEFAULT = EnumField("default", _("默认后端服务"))
    CUSTOM = EnumField("custom", _("自定义后端服务"))
    EXISTED = EnumField("existed", _("已存在的后端服务"))


class ServiceDiscoveryTypeEnum(StructuredEnum):
    """服务发现注册中心类型"""

    GO_MICRO_ETCD = EnumField("go_micro_etcd", "Go Micro - Etcd")


class EtcdSecureTypeEnum(StructuredEnum):
    """Etcd 安全认证类型"""

    SSL = EnumField("ssl", "SSL")
    PASSWORD = EnumField("password", "Password")


class SSLCertificateTypeEnum(StructuredEnum):
    """证书类型"""

    CLIENT = EnumField("client", _("客户端证书"))
    SERVER = EnumField("server", _("服务端证书"))
    CLIENT_REF = EnumField("client_ref", _("客户端引用证书"))
    SERVER_REF = EnumField("server_ref", _("服务端引用证书"))


class SSLCertificateBindingScopeTypeEnum(StructuredEnum):
    STAGE = EnumField("stage", _("环境"))
    STAGE_ITEM_CONFIG = EnumField("stage_item_config", _("环境配置"))
    BACKEND_SERVICE_DISCOVERY_CONFIG = EnumField("backend_service_discovery_config", _("后端服务发现配置"))


class GatewayTypeEnum(StructuredEnum):
    SUPER_OFFICIAL_API = EnumField(0, "超级官方API")
    OFFICIAL_API = EnumField(1, "官方云API")
    CLOUDS_API = EnumField(10, "云API")


class StageStatusEnum(StructuredEnum):
    INACTIVE = EnumField(0, "INACTIVE")
    ACTIVE = EnumField(1, "ACTIVE")


class ReleaseStatusEnum(StructuredEnum):
    SUCCESS = EnumField("success")  # 发布成功
    FAILURE = EnumField("failure")  # 发布失败
    PENDING = EnumField("pending")  # 待发布
    RELEASING = EnumField("releasing")  # 发布中
    UNRELEASED = EnumField("unreleased")  # 未发布


class PublishEventEnum(StructuredEnum):
    # dashboard
    VALIDATE_CONFIGURATION = EnumField("validata_configuration", "validate configuration")
    GENERATE_TASK = EnumField("generate_release_task", "generate release task")
    DISTRIBUTE_CONFIGURATION = EnumField("distribute_configuration", "distribute configuration")
    # operator
    PARSE_CONFIGURATION = EnumField("parse_configuration", "parse configuration")
    APPLY_CONFIGURATION = EnumField("apply_configuration", "apply configuration")
    # apisix
    LOAD_CONFIGURATION = EnumField("load_configuration", "load configuration")


# 因为 get_event_step 依赖字段顺序，所以继承 Enum，以便于 get_event_step 获取 step
class PublishEventNameTypeEnum(Enum):
    VALIDATE_CONFIGURATION = PublishEventEnum.VALIDATE_CONFIGURATION.value
    GENERATE_TASK = PublishEventEnum.GENERATE_TASK.value
    DISTRIBUTE_CONFIGURATION = PublishEventEnum.DISTRIBUTE_CONFIGURATION.value
    PARSE_CONFIGURATION = PublishEventEnum.PARSE_CONFIGURATION.value
    APPLY_CONFIGURATION = PublishEventEnum.APPLY_CONFIGURATION.value
    LOAD_CONFIGURATION = PublishEventEnum.LOAD_CONFIGURATION.value

    @classmethod
    def get_event_step(cls, name: str) -> int:
        # 获取事件所属的step，如：name="load configuration"==>5
        return [i.value for i in cls].index(name)


class PublishEventStatusEnum(StructuredEnum):
    SUCCESS = EnumField("success", "success")  # 执行成功
    FAILURE = EnumField("failure", "failure")  # 执行失败
    PENDING = EnumField("pending", "pending")  # 待执行
    DOING = EnumField("doing", "doing")  # 执行中


class PublishEventStatusTypeEnum(StructuredEnum):
    SUCCESS = EnumField(PublishEventStatusEnum.SUCCESS.value)
    FAILURE = EnumField(PublishEventStatusEnum.FAILURE.value)
    PENDING = EnumField(PublishEventStatusEnum.PENDING.value)
    DOING = EnumField(PublishEventStatusEnum.DOING.value)


class PublishSourceEnum(StructuredEnum):
    # gateway
    GATEWAY_ENABLE = EnumField("gateway_enable", "网关启用")
    GATEWAY_DISABLE = EnumField("gateway_disable", "网关停用")

    # version
    VERSION_PUBLISH = EnumField("version_publish", "版本发布")

    # plugin
    PLUGIN_BIND = EnumField("plugin_bind", "插件绑定")
    PLUGIN_UPDATE = EnumField("plugin_update", "插件更新")
    PLUGIN_UNBIND = EnumField("plugin_unbind", "插件解绑")

    # stage
    STAGE_DISABLE = EnumField("stage_disable", "环境下架")
    STAGE_DELETE = EnumField("stage_delete", "环境删除")
    STAGE_UPDATE = EnumField("stage_update", "环境更新")

    # backend
    BACKEND_UPDATE = EnumField("backend_update", "服务更新")

    # cli
    CLI_SYNC = EnumField("cli_sync", "命令行同步")


# 触发发布类型
class TriggerPublishTypeEnum(StructuredEnum):
    TRIGGER_ROLLING_UPDATE_RELEASE = EnumField("trigger_rolling_update_release", "滚动更新发布")
    TRIGGER_REVOKE_DISABLE_RELEASE = EnumField("trigger_revoke_disable_release", "停用/下架发布")
    TRIGGER_REVOKE_DELETE_RELEASE = EnumField("trigger_revoke_delete_release", "删除发布")


#  不同发布来源对应不同的触发发布类型
PublishSourceTriggerPublishTypeMapping = {
    # 滚动更新发布
    PublishSourceEnum.GATEWAY_ENABLE: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    PublishSourceEnum.STAGE_UPDATE: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    PublishSourceEnum.PLUGIN_UPDATE: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    PublishSourceEnum.PLUGIN_BIND: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    PublishSourceEnum.PLUGIN_UNBIND: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    PublishSourceEnum.BACKEND_UPDATE: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    PublishSourceEnum.CLI_SYNC: TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE,
    # 停用/下架发布
    PublishSourceEnum.GATEWAY_DISABLE: TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE,
    PublishSourceEnum.STAGE_DISABLE: TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE,
    # 删除发布
    PublishSourceEnum.STAGE_DELETE: TriggerPublishTypeEnum.TRIGGER_REVOKE_DELETE_RELEASE,
}


class ResourceVersionSchemaEnum(StructuredEnum):
    V1 = EnumField("1.0", "旧模型版本")
    V2 = EnumField("2.0", "新模型版本")


class ProxyTypeEnum(StructuredEnum):
    HTTP = EnumField("http", "http")
    MOCK = EnumField("mock", "mock")


class ScopeTypeEnum(StructuredEnum):
    GATEWAY = EnumField("api", _("网关"))
    STAGE = EnumField("stage", _("环境"))
    RESOURCE = EnumField("resource", _("资源"))


class ContextScopeTypeEnum(StructuredEnum):
    GATEWAY = EnumField(ScopeTypeEnum.GATEWAY.value)
    STAGE = EnumField(ScopeTypeEnum.STAGE.value)
    RESOURCE = EnumField(ScopeTypeEnum.RESOURCE.value)


class ContextTypeEnum(StructuredEnum):
    GATEWAY_AUTH = EnumField("api_auth")
    RESOURCE_AUTH = EnumField("resource_auth")
    STAGE_PROXY_HTTP = EnumField("stage_proxy_http")
    STAGE_RATE_LIMIT = EnumField("stage_rate_limit")
    GATEWAY_FEATURE_FLAG = EnumField("api_feature_flag")


class LoadBalanceTypeEnum(StructuredEnum):
    RR = EnumField("roundrobin", "RR")
    WRR = EnumField("weighted-roundrobin", "Weighted-RR")


HTTP_METHOD_ANY = "ANY"

HTTP_METHOD_CHOICES = [
    ("GET", "GET"),
    ("POST", "POST"),
    ("PUT", "PUT"),
    ("PATCH", "PATCH"),
    ("DELETE", "DELETE"),
    ("HEAD", "HEAD"),
    ("OPTIONS", "OPTIONS"),
]
RESOURCE_METHOD_CHOICES = HTTP_METHOD_CHOICES + [
    (HTTP_METHOD_ANY, HTTP_METHOD_ANY),
]


class BackendTypeEnum(StructuredEnum):
    HTTP = EnumField("http", label="HTTP")
    GRPC = EnumField("grpc", label="GRPC")


DEFAULT_STAGE_NAME = "prod"
DEFAULT_LB_HOST_WEIGHT = 100
DEFAULT_BACKEND_NAME = "default"

# Stage
STAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,19}$")
STAGE_VAR_REFERENCE_PATTERN = re.compile(r"env\.([a-zA-Z][a-zA-Z0-9_]{0,49})")
STAGE_VAR_PATTERN = re.compile(r"\{%s\}" % STAGE_VAR_REFERENCE_PATTERN.pattern)
# 为降低正则表达式复杂度，此 IPV6 正则并不完全准确，且作为访问地址，其应放在中括号中，例如：[2001:db8:3333:4444:5555:6666:7777:8888]:8000
DOMAIN_WITH_IPV6_PATTERN = re.compile(r"^\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?$")
# 不带 scheme 的服务地址
HOST_WITHOUT_SCHEME_PATTERN = re.compile(
    r"^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?$"
    + "|"
    + DOMAIN_WITH_IPV6_PATTERN.pattern
)

# 资源路径转换为名称正则
PATH_TO_NAME_PATTERN = re.compile(r"[a-zA-Z0-9]+")

# Micro gateway
MICRO_GATEWAY_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,19}$")
