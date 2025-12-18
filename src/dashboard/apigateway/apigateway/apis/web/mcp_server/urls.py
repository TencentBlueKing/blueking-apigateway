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
    MCPServerAppPermissionApplyApplicantListApi,
    MCPServerAppPermissionApplyListApi,
    MCPServerAppPermissionApplyUpdateStatusApi,
    MCPServerAppPermissionDestroyApi,
    MCPServerAppPermissionListCreateApi,
    MCPServerGuidelineRetrieveApi,
    MCPServerListCreateApi,
    MCPServerRemotePromptsListApi,
    MCPServerRetrieveUpdateDestroyApi,
    MCPServerStageReleaseCheckApi,
    MCPServerToolDocRetrieveApi,
    MCPServerToolsListApi,
    MCPServerUpdateLabelsApi,
    MCPServerUpdateStatusApi,
    MCPServerUserCustomDocApi,
)

urlpatterns = [
    # list or create gateway mcp server
    path("", MCPServerListCreateApi.as_view(), name="mcp_server.list_create"),
    path(
        "<int:mcp_server_id>/",
        include(
            [
                path("", MCPServerRetrieveUpdateDestroyApi.as_view(), name="mcp_server.retrieve_update_destroy"),
                path("status/", MCPServerUpdateStatusApi.as_view(), name="mcp_server.update_status"),
                path("labels/", MCPServerUpdateLabelsApi.as_view(), name="mcp_server.update_labels"),
                path(
                    "tools/",
                    include(
                        [
                            path("", MCPServerToolsListApi.as_view(), name="mcp_server.tools_list"),
                            path(
                                "<str:tool_name>/doc/",
                                MCPServerToolDocRetrieveApi.as_view(),
                                name="mcp_server.tool_doc_retrieve",
                            ),
                        ]
                    ),
                ),
                path("guideline/", MCPServerGuidelineRetrieveApi.as_view(), name="mcp_server.guideline_retrieve"),
                path(
                    "user-custom-doc/",
                    MCPServerUserCustomDocApi.as_view(),
                    name="mcp_server.user_custom_doc",
                ),
                path(
                    "permissions/",
                    include(
                        [
                            path(
                                "",
                                MCPServerAppPermissionListCreateApi.as_view(),
                                name="mcp_server.app-permission.list_create",
                            ),
                            path(
                                "<int:id>/",
                                MCPServerAppPermissionDestroyApi.as_view(),
                                name="mcp_server.app-permission.destroy",
                            ),
                            path(
                                "app-permission-apply/",
                                include(
                                    [
                                        path(
                                            "",
                                            MCPServerAppPermissionApplyListApi.as_view(),
                                            name="mcp_server.app-permission-apply.list",
                                        ),
                                        path(
                                            "applicant/",
                                            MCPServerAppPermissionApplyApplicantListApi.as_view(),
                                            name="mcp_server.app-permission-apply.applicant_list",
                                        ),
                                        path(
                                            "<int:id>/status/",
                                            MCPServerAppPermissionApplyUpdateStatusApi.as_view(),
                                            name="mcp_server.app-permission-apply.update_status",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path("-/stage-release-check/", MCPServerStageReleaseCheckApi.as_view(), name="mcp_server.stage_release_check"),
    path("-/remote-prompts/", MCPServerRemotePromptsListApi.as_view(), name="mcp_server.remote_prompts_list"),
]
