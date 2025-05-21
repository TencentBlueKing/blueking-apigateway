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

from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer


class TestMCPServer:
    def test_labels(self):
        mcp_server = G(MCPServer)
        assert mcp_server.labels == []

        mcp_server.labels = ["label1", "label2"]
        assert mcp_server.labels == ["label1", "label2"]

    def test_resource_ids(self):
        mcp_server = G(MCPServer)
        assert mcp_server.resource_names == []

        mcp_server.resource_names = ["resource1", "resource2"]
        assert mcp_server.resource_names == ["resource1", "resource2"]

    def test_is_active(self):
        mcp_server = G(MCPServer)
        assert mcp_server.is_active is False

        mcp_server.status = MCPServerStatusEnum.ACTIVE.value
        assert mcp_server.is_active is True

    def test_tools_count(self):
        mcp_server = G(MCPServer)
        assert mcp_server.tools_count == 0

        mcp_server.resource_names = ["resource1", "resource2"]
        assert mcp_server.tools_count == 2
