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
    }
