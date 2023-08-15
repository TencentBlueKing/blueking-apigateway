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


class StageItemTypeEnum(StructuredEnum):
    """环境配置项类型"""

    NODE = EnumField(BackendUpstreamTypeEnum.NODE.value, _("节点"))
    SERVICE_DISCOVERY = EnumField(BackendUpstreamTypeEnum.SERVICE_DISCOVERY.value, _("服务发现注册中心"))


class StageItemConfigStatusEnum(StructuredEnum):
    """环境配置项状态"""

    CONFIGURED = EnumField("configured", _("已配置"))
    NOT_CONFIGURED = EnumField("not_configured", _("待配置"))


class ServiceDiscoveryTypeEnum(StructuredEnum):
    """服务发现注册中心类型"""

    GO_MICRO_ETCD = EnumField("go_micro_etcd", "Go Micro - Etcd")


class PassHostEnum(StructuredEnum):
    """请求发给上游时的 host 设置选型"""

    PASS = EnumField("pass", _("保持与客户端请求一致的主机名"))
    NODE = EnumField("node", _("使用目标节点列表中的主机名或 IP"))
    REWRITE = EnumField("rewrite", _("自定义 Host 请求头"))


class SchemeEnum(StructuredEnum):
    """与后端服务通信时使用的 scheme"""

    # 7 层代理
    HTTP = EnumField("http", "HTTP")
    HTTPS = EnumField("https", "HTTPs")
    GRPC = EnumField("grpc", "gRPC")
    GRPCS = EnumField("grpcs", "gRPCs")


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

    @classmethod
    def is_official(cls, value: int) -> bool:
        return value in [cls.SUPER_OFFICIAL_API.value, cls.OFFICIAL_API.value]

    @property
    def sort_key(self):
        if self._value_ in [self.SUPER_OFFICIAL_API.value, self.OFFICIAL_API.value]:
            return "a"
        return "b"


class StageStatusEnum(ChoiceEnumMixin, Enum):
    INACTIVE = 0
    ACTIVE = 1


class ReleaseStatusEnum(ChoiceEnumMixin, Enum):
    SUCCESS = "success"  # 发布成功
    FAILURE = "failure"  # 发布失败
    PENDING = "pending"  # 待发布
    RELEASING = "releasing"  # 发布中


class PublishEventEnum(StructuredEnum):
    # dashboard
    GenerateTask = EnumField("generate_release_task", "generate release task")
    DistributeConfiguration = EnumField("distribute_configuration", "distribute configuration")
    # operator
    ParseConfiguration = EnumField("parse_configuration", "parse configuration")
    ApplyConfiguration = EnumField("apply_configuration", "apply configuration")
    # apisix
    LoadConfiguration = EnumField("load_configuration", "load configuration")


class PublishEventNameTypeEnum(ChoiceEnumMixin, Enum):
    GenerateTask = PublishEventEnum.GenerateTask.value
    DistributeConfiguration = PublishEventEnum.DistributeConfiguration.value
    ParseConfiguration = PublishEventEnum.ParseConfiguration.value
    ApplyConfiguration = PublishEventEnum.ApplyConfiguration.value
    LoadConfiguration = PublishEventEnum.LoadConfiguration.value

    @classmethod
    def get_event_step(cls, name: str) -> int:
        # 获取事件所属的step，如：name="load configuration"==>5
        return [i.value for i in cls].index(name) + 1


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


class ProxyTypeEnum(StructuredEnum):
    HTTP = EnumField("http", "http")
    MOCK = EnumField("mock", "mock")


class ScopeTypeEnum(StructuredEnum):
    API = EnumField("api", _("网关"))
    STAGE = EnumField("stage", _("环境"))
    RESOURCE = EnumField("resource", _("资源"))


class ContextScopeTypeEnum(ChoiceEnumMixin, Enum):
    API = ScopeTypeEnum.API.value
    STAGE = ScopeTypeEnum.STAGE.value
    RESOURCE = ScopeTypeEnum.RESOURCE.value


class ContextTypeEnum(ChoiceEnumMixin, Enum):
    API_AUTH = "api_auth"
    RESOURCE_AUTH = "resource_auth"
    STAGE_PROXY_HTTP = "stage_proxy_http"
    STAGE_RATE_LIMIT = "stage_rate_limit"
    API_FEATURE_FLAG = "api_feature_flag"


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


class ExportTypeEnum(ChoiceEnumMixin, Enum):
    # 全部资源
    ALL = "all"
    # 已筛选资源
    FILTERED = "filtered"
    # 已选资源
    SELECTED = "selected"


class SwaggerFormatEnum(StructuredEnum):
    YAML = EnumField("yaml", label="YAML")
    JSON = EnumField("json", label="JSON")


# 每个资源允许关联的最大标签个数
MAX_LABEL_COUNT_PER_RESOURCE = 10

DEFAULT_STAGE_NAME = "prod"
DEFAULT_LB_HOST_WEIGHT = 100

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

# 单位为秒的持续时间
DURATION_IN_SECOND_PATTERN = re.compile(r"^(\d+)s$")

# 超时时间设置
MAX_BACKEND_TIMEOUT_IN_SECOND = 600
MAX_CONNECT_TIMEOUT_IN_SECOND = 600
MAX_SEND_TIMEOUT_IN_SECOND = 600
MAX_READ_TIMEOUT_IN_SECOND = 600
