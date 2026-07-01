# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
import json

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerExtendTypeEnum
from apigateway.apps.mcp_server.management.commands.fix_invalid_mcp_prompts import Command
from apigateway.apps.mcp_server.models import MCPServer, MCPServerExtend

pytestmark = pytest.mark.django_db


class TestCommand:
    def test_default_mode_fallback_to_dry_run(self, fake_gateway, fake_stage, capsys):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        extend = G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content='{"test":"2"',
        )

        Command().handle(dry_run=False, apply=False, mcp_server_ids="", updated_by="system")

        extend.refresh_from_db()
        captured = capsys.readouterr()
        assert "No mode specified, fallback to --dry-run." in captured.out
        assert "Dry run mode: no data changed." in captured.out
        assert extend.content == '{"test":"2"'

    def test_dry_run_only_list_invalid(self, fake_gateway, fake_stage, capsys):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        extend = G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content='{"test":"2"',
        )

        Command().handle(dry_run=True, apply=False, mcp_server_ids="", updated_by="system")

        extend.refresh_from_db()
        captured = capsys.readouterr()
        assert f"mcp_server_id={mcp_server.id}" in captured.out
        assert "Dry run mode: no data changed." in captured.out
        assert extend.content == '{"test":"2"'

    def test_apply_fix_with_mcp_server_ids_filter(self, fake_gateway, fake_stage):
        mcp_server1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        extend1 = G(
            MCPServerExtend,
            mcp_server=mcp_server1,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content='{"test":"2"',
            updated_by="old-user",
        )
        extend2 = G(
            MCPServerExtend,
            mcp_server=mcp_server2,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content='{"test":"3"',
            updated_by="old-user",
        )

        Command().handle(
            dry_run=False,
            apply=True,
            mcp_server_ids=str(mcp_server1.id),
            updated_by="fix-user",
        )

        extend1.refresh_from_db()
        extend2.refresh_from_db()
        assert json.loads(extend1.content) == []
        assert extend1.updated_by == "fix-user"
        assert extend2.content == '{"test":"3"'
        assert extend2.updated_by == "old-user"

    def test_apply_fix_for_invalid_payload_structure(self, fake_gateway, fake_stage):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        extend = G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps({"id": 1}),
            updated_by="old-user",
        )

        Command().handle(
            dry_run=False,
            apply=True,
            mcp_server_ids=str(mcp_server.id),
            updated_by="fix-user",
        )

        extend.refresh_from_db()
        assert json.loads(extend.content) == []
        assert extend.updated_by == "fix-user"
