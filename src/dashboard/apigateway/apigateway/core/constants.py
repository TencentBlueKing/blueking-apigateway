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

from blue_krill.data_types.enum import EnumField, FeatureFlag, FeatureFlagField, StructuredEnum
from django.utils.translation import gettext_lazy as _

from apigateway.common.constants import ChoiceEnumMixin


class UserAuthTypeEnum(ChoiceEnumMixin, Enum):
    IEOD = "ieod"
    TENCENT = "tencent"
    DEFAULT = "default"


class GatewayStatusEnum(StructuredEnum):
    INACTIVE = EnumField(0, "已停用")
    ACTIVE = EnumField(1, "启用中")


# TODO: delete it
class APIHostingTypeEnum(StructuredEnum):
    """网关托管类型，影响特性集"""

    DEFAULT = EnumField(0, "apigateway-ng")
    MICRO = EnumField(1, _("微网关"))


class GatewayFeatureFlag(FeatureFlag):
    """通用网关特性开关"""

    ENABLE_I18N_SUPPORT = FeatureFlagField("ENABLE_I18N_SUPPORT", "是否启用国际化支持", False)


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


class ReleaseStatusEnum(ChoiceEnumMixin, Enum):
    SUCCESS = "success"  # 发布成功
    FAILURE = "failure"  # 发布失败
    PENDING = "pending"  # 待发布
    RELEASING = "releasing"  # 发布中


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


class PublishEventNameTypeEnum(ChoiceEnumMixin, Enum):
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


class PublishEventStatusTypeEnum(ChoiceEnumMixin, Enum):
    SUCCESS = PublishEventStatusEnum.SUCCESS.value
    FAILURE = PublishEventStatusEnum.FAILURE.value
    PENDING = PublishEventStatusEnum.PENDING.value
    DOING = PublishEventStatusEnum.DOING.value


class PublishSourceEnum(StructuredEnum):
    # gateway
    GATEWAY_ENABLE = EnumField("gateway_enable", "网关启用")
    GATEWAY_DISABLE = EnumField("gateway_disable", "网关停用")

    # version
    VERSION_PUBLISH = EnumField("version_publish", "版本发布")

    # plugin
    PLUGIN_UPDATE = EnumField("plugin_update", "插件更新")

    # stage
    STAGE_DISABLE = EnumField("stage_disable", "环境下架")
    STAGE_UPDATE = EnumField("stage_env_update", "环境更新")

    # backend
    BACKEND_UPDATE = EnumField("backend_update", "服务更新")

    # cli
    CLI_SYNC = EnumField("cli_sync", "命令行同步")


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


# 资源导出 Swagger 配置中的扩展字段名
class SwaggerExtensionEnum(ChoiceEnumMixin, Enum):
    METHOD_ANY = "x-bk-apigateway-method-any"
    RESOURCE = "x-bk-apigateway-resource"


VALID_METHOD_IN_SWAGGER_PATHITEM = [
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    SwaggerExtensionEnum.METHOD_ANY.value,
]


class ExportTypeEnum(StructuredEnum):
    # 全部资源
    ALL = EnumField("all")
    # 已筛选资源
    FILTERED = EnumField("filtered")
    # 已选资源
    SELECTED = EnumField("selected")


class SwaggerFormatEnum(StructuredEnum):
    YAML = EnumField("yaml", label="YAML")
    JSON = EnumField("json", label="JSON")


class BackendTypeEnum(StructuredEnum):
    HTTP = EnumField("http", label="HTTP")
    GRPC = EnumField("grpc", label="GRPC")


# 每个资源允许关联的最大标签个数
MAX_LABEL_COUNT_PER_RESOURCE = 10

DEFAULT_STAGE_NAME = "prod"
DEFAULT_LB_HOST_WEIGHT = 100
DEFAULT_BACKEND_NAME = "default"

# 网关名
GATEWAY_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,29}$")

# Stage
STAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,19}$")
STAGE_VAR_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,49}$")
STAGE_VAR_REFERENCE_PATTERN = re.compile(r"env\.([a-zA-Z][a-zA-Z0-9_]{0,49})")
STAGE_VAR_PATTERN = re.compile(r"\{%s\}" % STAGE_VAR_REFERENCE_PATTERN.pattern)
STAGE_VAR_FOR_PATH_PATTERN = re.compile(r"^[\w/.-]*$")
# 为降低正则表达式复杂度，此 IPV6 正则并不完全准确，且作为访问地址，其应放在中括号中，例如：[2001:db8:3333:4444:5555:6666:7777:8888]:8000
DOMAIN_WITH_IPV6_PATTERN = re.compile(r"^\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?$")
DOMAIN_WITH_HTTP_AND_IPV6_PATTERN = re.compile(
    r"^http(s)?:\/\/\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?\/?$"
)
# 不带 scheme 的服务地址
HOST_WITHOUT_SCHEME_PATTERN = re.compile(
    r"^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?$"
    + "|"
    + DOMAIN_WITH_IPV6_PATTERN.pattern
)
STAGE_ITEM_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,49}$")

# 路径变量正则
PATH_PATTERN = re.compile(r"^/[\w{}/.-]*$")
PATH_VAR_PATTERN = re.compile(r"\{(.*?)\}")
# 通常的路径变量，如 {project_id}
NORMAL_PATH_VAR_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,29}$")
# 环境中包含环境变量，如 {env.prefix}
STAGE_PATH_VAR_NAME_PATTERN = re.compile(r"^%s$" % STAGE_VAR_REFERENCE_PATTERN.pattern)

# 资源正则
RESOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,255}$")
# 资源路径转换为名称正则
PATH_TO_NAME_PATTERN = re.compile(r"[a-zA-Z0-9]+")

DOMAIN_PATTERN = re.compile(
    r"^(?=^.{3,255}$)http(s)?:\/\/[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?\/?$"
    + "|"
    + DOMAIN_WITH_HTTP_AND_IPV6_PATTERN.pattern
)
RESOURCE_DOMAIN_PATTERN = re.compile(
    r"%s|%s|^http(s)?:\/\/\{%s\}$"
    % (DOMAIN_PATTERN.pattern, DOMAIN_WITH_HTTP_AND_IPV6_PATTERN.pattern, STAGE_VAR_REFERENCE_PATTERN.pattern)
)

HEADER_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9-]{1,100}$")

# Semver
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# bk app code
APP_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")

# Micro gateway
MICRO_GATEWAY_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,19}$")

# 后端服务名称
BACKEND_SERVICE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,29}$")

# 超时时间设置
MAX_BACKEND_TIMEOUT_IN_SECOND = 600
MAX_CONNECT_TIMEOUT_IN_SECOND = 600
MAX_SEND_TIMEOUT_IN_SECOND = 600
MAX_READ_TIMEOUT_IN_SECOND = 600
