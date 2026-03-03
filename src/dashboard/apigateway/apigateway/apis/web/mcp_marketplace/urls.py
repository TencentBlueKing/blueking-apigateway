# -*- coding: utf-8 -*-
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
from django.urls import include, path

from .views import (
    MCPMarketplaceCategoryListApi,
    MCPMarketplaceServerConfigListApi,
    MCPMarketplaceServerListApi,
    MCPMarketplaceServerRetrieveApi,
    MCPMarketplaceServerToolDocRetrieveApi,
)

urlpatterns = [
    # 分类列表
    path("categories/", MCPMarketplaceCategoryListApi.as_view(), name="mcp_marketplace.category.list"),
    path(
        "servers/",
        include(
            [
                # list or create gateway mcp server
                path("", MCPMarketplaceServerListApi.as_view(), name="mcp_marketplace.server.list"),
                path(
                    "<int:mcp_server_id>/",
                    include(
                        [
                            path(
                                "",
                                MCPMarketplaceServerRetrieveApi.as_view(),
                                name="mcp_marketplace.server.retrieve",
                            ),
                            path(
                                "configs/",
                                MCPMarketplaceServerConfigListApi.as_view(),
                                name="mcp_marketplace.server.config_list",
                            ),
                            path(
                                "tools/<str:tool_name>/doc/",
                                MCPMarketplaceServerToolDocRetrieveApi.as_view(),
                                name="mcp_marketplace.server.tool_doc_retrieve",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
