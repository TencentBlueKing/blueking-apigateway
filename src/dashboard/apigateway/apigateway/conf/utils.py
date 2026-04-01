# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import socket
from typing import Optional

from django.utils.functional import cached_property

from apigateway.common.env import Env


def get_default_keepalive_options() -> Optional[dict]:
    """Mac OS's socket module does not has below attrs, return empty options instead"""
    try:
        return {
            socket.TCP_KEEPIDLE: 60,
            socket.TCP_KEEPINTVL: 10,
            socket.TCP_KEEPCNT: 6,
        }
    except AttributeError:
        return None


class PatchFeatures:
    @cached_property
    def minimum_database_version(self):
        if self.connection.mysql_is_mariadb:
            return (10, 4)
        return (5, 7)


def get_plugin_metadata_config(env: Env) -> dict:
    return {
        "file-logger": {
            "log_format": {
                # 请求信息
                "proto": "$server_protocol",
                "method": "$request_method",
                "http_host": "$host",
                "http_path": "$uri",
                # "headers": "-",
                "params": "$args",
                "body": "$bk_log_request_body",
                "app_code": "$bk_app_code",
                "client_ip": "$remote_addr",
                "request_id": "$bk_request_id",
                "x_request_id": "$x_request_id",
                "request_duration": "$bk_log_request_duration",
                "bk_username": "$bk_username",
                "bk_tenant_id": "$bk_tenant_id",
                # 网关信息
                # FIXME: remove api_id and api_name, from 1.23
                # FIXME: change the access_log filter / metrics filter to gateway_id and gateway_name, from 1.23
                "api_id": "$bk_gateway_id",
                "api_name": "$bk_gateway_name",
                # rename to gateway_id and gateway_name, from 1.19
                "gateway_id": "$bk_gateway_id",
                "gateway_name": "$bk_gateway_name",
                "resource_id": "$bk_resource_id",
                "resource_name": "$bk_resource_name",
                "stage": "$bk_stage_name",
                # 后端服务
                "backend_name": "$bk_backend_name",
                "backend_scheme": "$upstream_scheme",
                "backend_method": "$method",
                # 后端服务 Host，即后端服务配置中的域名或 IP+Port
                "backend_host": "$bk_backend_host",
                # 后端服务地址，请求后端时，实际请求的 IP+Port，若后端服务配置中为域名，则为域名解析后的地址
                "backend_addr": "$upstream_addr",
                "backend_path": "$bk_log_backend_path",
                "backend_duration": "$bk_log_upstream_duration",
                # 响应
                "response_body": "$bk_log_response_body",
                "response_size": "$body_bytes_sent",
                "status": "$status",
                # 其它
                "msg": "-",
                "level": "info",
                "code_name": "$bk_apigw_error_code_name",
                "error": "$bk_apigw_error_message",
                "proxy_error": "$proxy_error",
                "instance": "$instance_id",
                "timestamp": "$bk_log_request_timestamp",
                # 临时字段，用于记录请求时，认证参数的位置，便于推动认证参数优化
                "auth_location": "$auth_params_location",
                # opentelemetry traceparent
                "traceparent": "$http_traceparent",
            }
        },
        "bk-concurrency-limit": {
            "conn": env.int("GATEWAY_CONCURRENCY_LIMIT_CONN", 2000),
            "burst": env.int("GATEWAY_CONCURRENCY_LIMIT_BURST", 1000),
            "default_conn_delay": env.int("GATEWAY_CONCURRENCY_LIMIT_DEFAULT_CONN_DELAY", 1),  # second
            "key_type": "var",
            "key": "bk_concurrency_limit_key",
            "allow_degradation": True,
        },
        "bk-real-ip": {
            "recursive": env.bool("GATEWAY_REAL_IP_RECURSIVE", False),
            "source": env.str("GATEWAY_REAL_IP_SOURCE", "http_x_forwarded_for"),
            "trusted_addresses": env.list("GATEWAY_REAL_IP_TRUSTED_ADDRESSES", default=["127.0.0.1", "::1"]),
        },
        "bk-opentelemetry": {
            "sampler": {
                # change to always_off/always_on/parent_base if needed!
                "name": env.str("GATEWAY_OTEL_SAMPLER_NAME", "always_off"),
                "options": {
                    "root": {
                        "name": "trace_id_ratio",
                        "options": {"fraction": env.float("GATEWAY_OTEL_ROOT_SAMPLER_RATIO", default=0.01)},
                    }
                },
            },
            "additional_attributes": [],
        },
    }


def get_gateway_quota_config(env: Env) -> dict:
    max_stage_count_per_gateway = env.int("MAX_STAGE_COUNT_PER_GATEWAY", 20)

    api_gateway_resource_limits = {
        "max_gateway_count_per_app": env.int("MAX_GATEWAY_COUNT_PER_APP", 10),  # 每个 app 最多创建的网关数量
        "max_resource_count_per_gateway": env.int(
            "MAX_RESOURCE_COUNT_PER_GATEWAY", 1000
        ),  # 每个网关最多创建的 api 数量
        "max_gateway_count_per_app_whitelist": {
            "bk_sops": 1000000,  # 标准运维网关数量无限制
            "data": 1000000,
        },
        "max_resource_count_per_gateway_whitelist": {
            "bk-esb": 5000,
            "bk-base": 2000,
        },
    }
    for k, v in env.dict("MAX_GATEWAY_COUNT_PER_APP_WHITELIST", default={}).items():
        api_gateway_resource_limits["max_gateway_count_per_app_whitelist"][k] = int(v)
    for k, v in env.dict("MAX_RESOURCE_COUNT_PER_GATEWAY_WHITELIST", default={}).items():
        api_gateway_resource_limits["max_resource_count_per_gateway_whitelist"][k] = int(v)

    return {
        "MAX_STAGE_COUNT_PER_GATEWAY": max_stage_count_per_gateway,
        "API_GATEWAY_RESOURCE_LIMITS": api_gateway_resource_limits,
        "MAX_LABEL_COUNT_PER_GATEWAY": env.int("MAX_LABEL_COUNT_PER_GATEWAY", 100),
        "MAX_BACKEND_TIMEOUT_IN_SECOND": env.int("MAX_BACKEND_TIMEOUT_IN_SECOND", 600),
        "MAX_PYTHON_SDK_COUNT_PER_RESOURCE_VERSION": env.int("MAX_PYTHON_SDK_COUNT_PER_RESOURCE_VERSION", 99),
    }


def get_default_feature_flags(
    env: Env,
    enable_bk_notice: bool,
    enable_multi_tenant_mode: bool,
    ai_open_api_base_url: str,
    enable_gateway_operation_status: bool,
    enable_run_data_metrics: bool,
) -> dict:
    return {
        # 是否展示"监控告警"子菜单
        "ENABLE_MONITOR": env.bool("FEATURE_FLAG_ENABLE_MONITOR", False),
        # 是否展示"运行数据"子菜单
        "ENABLE_RUN_DATA": env.bool("FEATURE_FLAG_ENABLE_RUN_DATA", False),
        # 是否展示 "运行数据" => 仪表盘 子菜单
        "ENABLE_RUN_DATA_METRICS": enable_run_data_metrics,
        # 是否展示"组件管理"菜单项，企业版展示，上云版不展示
        "MENU_ITEM_ESB_API": env.bool("FEATURE_FLAG_MENU_ITEM_ESB_API", True),
        # TODO: remove in the future, and remove in the helm-chart and te repo
        # 是否展示"组件 API 文档"菜单项
        "MENU_ITEM_ESB_API_DOC": env.bool("FEATURE_FLAG_MENU_ITEM_ESB_API_DOC", True),
        # 是否将 ESB 数据同步到网关。需要考虑这个是否还需要
        "SYNC_ESB_TO_APIGW_ENABLED": env.bool("FEATURE_FLAG_SYNC_ESB_TO_APIGW_ENABLED", True),
        # 网关编辑页，是否支持填写网关"绑定应用"
        "GATEWAY_APP_BINDING_ENABLED": env.bool("FEATURE_FLAG_GATEWAY_APP_BINDING_ENABLED", False),
        # FIXME: 为什么有两个 SDK 特性变量，并且容器化版本有 bkrepo 配置的话，默认应该都是 true?
        # 为 False，表示不启用 SDK 功能，网关 API 文档、组件 API 文档中，不展示 SDK 相关页面，
        # 隐藏"网关 APISDK"、"组件 APISDK"菜单项，隐藏网关中 SDK 创建、SDK 列表等功能项
        "ENABLE_SDK": env.bool("FEATURE_FLAG_ENABLE_SDK", False),
        # 隐藏 SDK 列表 相关功能
        "ALLOW_UPLOAD_SDK_TO_REPOSITORY": env.bool("FEATURE_FLAG_ALLOW_UPLOAD_SDK_TO_REPOSITORY", False),
        # 是否允许创建企业微信群，上云版一键拉群功能
        "ALLOW_CREATE_APPCHAT": env.bool("FEATURE_FLAG_ALLOW_CREATE_APPCHAT", False),
        # ----------------------------------------------------------------------------
        # 是否展示蓝鲸通知中心组件
        "ENABLE_BK_NOTICE": enable_bk_notice,
        # 是否开启多租户模式
        "ENABLE_MULTI_TENANT_MODE": enable_multi_tenant_mode,
        # 是否开启网关 AI 相关功能
        "ENABLE_AI_COMPLETION": ai_open_api_base_url != "",
        # 前端是否渲染 display_name
        "ENABLE_DISPLAY_NAME_RENDER": (
            enable_multi_tenant_mode or env.bool("FEATURE_FLAG_ENABLE_DISPLAY_NAME_RENDER", True)
        ),
        # 是否展示网关运营状态
        "ENABLE_GATEWAY_OPERATION_STATUS": enable_gateway_operation_status,
        # 是否启用 MCP Prompt 功能
        "ENABLE_MCP_SERVER_PROMPT": env.bool("FEATURE_FLAG_ENABLE_MCP_SERVER_PROMPT", False),
        # 是否启用健康检查
        "ENABLE_HEALTH_CHECK": env.bool("FEATURE_FLAG_ENABLE_HEALTH_CHECK", False),
        # 是否开启 MCP Server OAuth2 公开客户端模式
        "ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT": env.bool(
            "FEATURE_FLAG_ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT", True
        ),
        # 是否启用 MCP Server 可观测功能（指标、日志查询）
        "ENABLE_MCP_SERVER_OBSERVABLE": env.bool("FEATURE_FLAG_ENABLE_MCP_SERVER_OBSERVABLE", False),
    }


def get_frontend_env_vars(
    env: Env,
    edition: str,
    bk_app_code: str,
    default_test_app_code: str,
    bk_api_url_tmpl: str,
    bk_component_api_url: str,
    dashboard_fe_url: str,
    dashboard_url: str,
    csrf_cookie_name: str,
    csrf_cookie_domain: str,
    bk_apigateway_version: str,
    bk_docs_url_prefix: str,
    bk_login_url: str,
) -> dict:
    return {
        "EDITION": edition,
        "BK_APP_CODE": bk_app_code,
        "BK_DEFAULT_TEST_APP_CODE": default_test_app_code,
        "BK_API_RESOURCE_URL_TMPL": bk_api_url_tmpl + "/{stage_name}/{resource_path}",
        "BK_COMPONENT_API_URL": bk_component_api_url,
        "BK_PAAS_APP_REPO_URL_TMPL": env.str(
            "BK_PAAS_APP_REPO_URL_TMPL", "https://example.com/groups/blueking-plugins/apigw/{{gateway_name}}.git"
        ),
        "BK_DASHBOARD_FE_URL": dashboard_fe_url,
        "BK_DASHBOARD_URL": dashboard_url,
        "BK_DASHBOARD_CSRF_COOKIE_NAME": csrf_cookie_name,
        "BK_DASHBOARD_CSRF_COOKIE_DOMAIN": csrf_cookie_domain,
        "BK_DASHBOARD_COOKIE_DOMAIN": csrf_cookie_domain,
        "BK_APIGATEWAY_VERSION": bk_apigateway_version,
        "BK_DOCS_URL_PREFIX": bk_docs_url_prefix,
        "BK_USER_WEB_API_URL": bk_api_url_tmpl.format(api_name="bk-user-web") + "/prod",
        "BK_LOGIN_URL": bk_login_url,
        "BK_APISIX_URL": env.str("BK_APISIX_URL", default=""),
        "BK_APISIX_DOC_URL": env.str("BK_APISIX_DOC_URL", default=""),
        "BK_ANALYSIS_SCRIPT_SRC": env.str("BK_ANALYSIS_SCRIPT_SRC", default=""),
        "CREATE_CHAT_API": env.str("CREATE_CHAT_API", default=""),
        "SEND_CHAT_API": env.str("SEND_CHAT_API", default=""),
        "HELPER": {
            "name": env.str("HELPER_NAME", default=""),
            "href": env.str("HELPER_HREF", default=""),
        },
        "BK_SHARED_RES_URL": env.str("BK_SHARED_RES_URL", default=""),
    }


def get_bkrepo_config(env: Env) -> dict:
    return {
        "BKREPO_ENDPOINT_URL": env.str("BKREPO_ENDPOINT_URL", ""),
        "BKREPO_USERNAME": env.str("BKREPO_USERNAME", "bk_apigateway"),
        "BKREPO_PASSWORD": env.str("BKREPO_PASSWORD", ""),
        "BKREPO_PROJECT": env.str("BKREPO_PROJECT", "bk_apigateway"),
        "BKREPO_GENERIC_BUCKET": env.str("BKREPO_GENERIC_BUCKET", "generic"),
        "PYPI_MIRRORS_CONFIG": {
            "default": {
                "repository_url": env.str("DEFAULT_PYPI_REPOSITORY_URL", ""),
                "index_url": env.str("DEFAULT_PYPI_INDEX_URL", ""),
                "username": env.str("DEFAULT_PYPI_USERNAME", ""),
                "password": env.str("DEFAULT_PYPI_PASSWORD", ""),
            }
        },
        "PYPI_MIRRORS_REPOSITORY": env.str("PYPI_INDEX_URL", "https://pypi.org/simple/"),
        "MAVEN_MIRRORS_CONFIG": {
            "default": {
                "repository_url": env.str("DEFAULT_MAVEN_REPOSITORY_URL", ""),
                "repository_id": env.str("DEFAULT_MAVEN_REPOSITORY_ID", "bkpaas-maven"),
                "username": env.str("DEFAULT_MAVEN_USERNAME", "bk_apigateway"),
                "password": env.str("DEFAULT_MAVEN_PASSWORD", "bk_apigateway"),
                "ssl_insecure": env.bool("DEFAULT_MAVEN_SSL_INSECURE", False),
                "mirror_url": env.str("DEFAULT_MAVEN_MIRROR_URL", ""),
            }
        },
    }


def get_doc_links(bk_apigw_version: str, bk_docs_url_prefix: str, lang: str = "ZH") -> dict:
    env = Env()
    version = ".".join(bk_apigw_version.split(".")[:2])
    doc_link_prefix = f"{bk_docs_url_prefix}/markdown/{lang}/APIGateway/{version}"
    return {
        # 使用指南
        "GUIDE": env.str("DOC_LINK_GUIDE", default=f"{doc_link_prefix}/UserGuide/README.md"),
        #  “请求流水查询规则”
        "QUERY_USE": env.str("DOC_LINK_QUERY_USE", default=f"{doc_link_prefix}/UserGuide/Explanation/access-log.md"),
        # 蓝鲸用户认证
        "USER_VERIFY": env.str(
            "DOC_LINK_USER_VERIFY", default=f"{doc_link_prefix}/UserGuide/Explanation/authorization.md"
        ),
        # API 资源模板变量
        "TEMPLATE_VARS": env.str(
            "DOC_LINK_TEMPLATE_VARS", default=f"{doc_link_prefix}/UserGuide/Explanation/template-var.md"
        ),
        # 网关认证
        "AUTH": env.str("DOC_LINK_AUTH", default=f"{doc_link_prefix}/UserGuide/Explanation/authorization.md"),
        # 负载均衡
        "LOADBALANCE": env.str(
            "DOC_LINK_LOADBALANCE", default=f"{doc_link_prefix}/UserGuide/Explanation/loadbalance.md"
        ),
        # Swagger 说明文档
        "SWAGGER": env.str(
            "DOC_LINK_SWAGGER", default=f"{doc_link_prefix}/UserGuide/HowTo/Connect/swagger-explain.md"
        ),
        # 跨域资源共享 (CORS)
        "CORS": env.str("DOC_LINK_CORS", default=f"{doc_link_prefix}/UserGuide/HowTo/Plugins/cors.md"),
        # 频率控制
        "RATELIMIT": env.str("DOC_LINK_RATELIMIT", default=f"{doc_link_prefix}/UserGuide/HowTo/Plugins/rate-limit.md"),
        # JWT
        "JWT": env.str("DOC_LINK_JWT", default=f"{doc_link_prefix}/UserGuide/Explanation/jwt.md"),
        # API 网关错误码
        "ERROR_CODE": env.str("DOC_LINK_ERROR_CODE", default=f"{doc_link_prefix}/UserGuide/FAQ/error-response.md"),
        # 组件频率控制
        "COMPONENT_RATE_LIMIT": env.str(
            "DOC_LINK_COMPONENT_RATE_LIMIT", default=f"{doc_link_prefix}/component/reference/rate-limit.md"
        ),
        # 如何开发和发布组件
        "COMPONENT_CREATE_API": env.str(
            "DOC_LINK_COMPONENT_CREATE_API", default=f"{doc_link_prefix}/component/quickstart/create-api.md"
        ),
        # 文档导入详情
        "IMPORT_RESOURCE_DOCS": env.str(
            "DOC_LINK_IMPORT_RESOURCE_DOCS", default=f"{doc_link_prefix}/UserGuide/HowTo/Connect/manage-document.md"
        ),
        # 调用 API
        "USER_API": env.str("DOC_LINK_USER_API", default=f"{doc_link_prefix}/UserGuide/HowTo/call-gateway-api.md"),
        # 升级到 1.13 的指引说明
        "UPGRADE_TO_113_TIP": env.str("DOC_LINK_UPGRADE_TO_113_TIP", default=""),
        # mcp 权限申请指引
        "MCP_SERVER_PERMISSION_APPLY": env.str(
            "DOC_LINK_MCP_SERVER_PERMISSION_APPLY",
            default=f"{doc_link_prefix}/UserGuide/HowTo/apply-mcp-server-permission.md",
        ),
        # bk-cors
        "PLUGIN_BK_CORS": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-cors.md",
        # bk-ip-restriction
        "PLUGIN_BK_IP_RESTRICTION": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-ip-restriction.md",
        # bk-rate-limit
        "PLUGIN_BK_RATE_LIMIT": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-rate-limit.md",
        # bk-header-rewrite
        "PLUGIN_BK_HEADER_REWRITE": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-header-rewrite.md",
        # bk-mock
        "PLUGIN_BK_MOCK": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-mock.md",
        # api-breaker
        "PLUGIN_API_BREAKER": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/api-breaker.md",
        # request-validation
        "PLUGIN_REQUEST_VALIDATION": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/request-validation.md",
        # fault-injection
        "PLUGIN_FAULT_INJECTION": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/fault-injection.md",
        # response-rewrite
        "PLUGIN_RESPONSE_REWRITE": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/response-rewrite.md",
        # redirect
        "PLUGIN_REDIRECT": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/redirect.md",
        # bk-access-token-source
        "PLUGIN_BK_ACCESS_TOKEN_SOURCE": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-access-token-source.md",
        # bk-username-required
        "PLUGIN_BK_USERNAME_REQUIRED": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-username-required.md",
        # bk-request-body-limit
        "PLUGIN_BK_REQUEST_BODY_LIMIT": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-request-body-limit.md",
        # bk-user-restriction
        "PLUGIN_BK_USER_RESTRICTION": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/bk-user-restriction.md",
        # proxy-cache
        "PLUGIN_PROXY_CACHE": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/proxy-cache.md",
        # ai-proxy
        "PLUGIN_AI_PROXY": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/ai-proxy.md",
        # ai-rate-limiting
        "PLUGIN_AI_RATE_LIMITING": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/ai-rate-limiting.md",
        # uri-blocker
        "PLUGIN_URI_BLOCKER": f"{doc_link_prefix}/UserGuide/HowTo/Plugins/uri-blocker.md",
    }


def get_esb_board_configs(env: Env, *, bk_component_api_url: str) -> dict:
    # django translation, 避免循环引用
    gettext = lambda s: s  # noqa

    return {
        "default": {
            "name": "default",
            "label": gettext("蓝鲸智云"),
            "api_envs": [
                {
                    "name": "prod",
                    "label": gettext("正式环境"),
                    "host": env.str("ESB_DEFAULT_BOARD_PROD_URL", "") or bk_component_api_url,
                    "description": gettext("访问后端正式环境"),
                },
                {
                    "name": "test",
                    "label": gettext("测试环境"),
                    "host": env.str("ESB_DEFAULT_BOARD_TEST_URL", ""),
                    "description": gettext("访问后端测试环境"),
                },
            ],
            "has_sdk": env.bool("ESB_DEFAULT_BOARD_HAS_SDK", True),
            "sdk_name": "bkapi-component-open",
            "sdk_package_prefix": "bkapi_component.open",
            "sdk_doc_templates": {
                "python_sdk_usage_example": "python_sdk_usage_example_v2.md",
            },
            "sdk_description": gettext("访问蓝鲸智云组件 API"),
        },
    }
