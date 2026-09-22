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
import os
import subprocess
import sys
from pathlib import Path

import pytest

DASHBOARD = Path(__file__).resolve().parents[4]
PROJECT = DASHBOARD / "apigateway"
CASES = [
    ("ee", None, "false", True),
    ("ee", "true", "false", True),
    ("ee", "false", "false", False),
    ("ee", "False", "false", False),
    ("te", "false", "false", True),
    ("ee", "true", "true", False),
    ("ee", "false", "True", False),
    ("te", "False", "false", True),
    ("te", "false", "true", False),
]


def runtime_env(edition, enabled, multi_tenant):
    env = dict(os.environ, EDITION=edition, ENABLE_MULTI_TENANT_MODE=multi_tenant, BKPAAS_ENVIRONMENT="prod")
    env.pop("ENABLE_ESB", None)
    if enabled is not None:
        env["ENABLE_ESB"] = enabled
    return env


@pytest.mark.parametrize("flag_enabled", ["true", "false"])
@pytest.mark.parametrize("edition, enabled, multi_tenant, expected", CASES)
def test_esb_runtime_registration(edition, enabled, multi_tenant, expected, flag_enabled):
    # Run fresh Django startup so cached settings/URL imports cannot hide a broken guard.
    code = """
import importlib
import json
import django
from django.conf import settings
from django.urls import get_resolver
from django.urls.resolvers import URLResolver

django.setup()

def routes(patterns):
    result = []
    for pattern in patterns:
        result.append(str(pattern.pattern))
        if isinstance(pattern, URLResolver):
            result.extend(routes(pattern.url_patterns))
    return result

for task_module in settings.CELERY_IMPORTS:
    importlib.import_module(task_module)
print(json.dumps({
    "database": "bkcore" in settings.DATABASES,
    "app": "apigateway.apps.esb.bkcore" in settings.INSTALLED_APPS,
    "task": "apigateway.apps.esb.component.tasks" in settings.CELERY_IMPORTS,
    "routes": any("esb/" in route for route in routes(get_resolver().url_patterns)),
    "flags": {key: settings.DEFAULT_FEATURE_FLAG[key] for key in (
        "MENU_ITEM_ESB_API", "MENU_ITEM_ESB_API_DOC", "SYNC_ESB_TO_APIGW_ENABLED"
    )},
}))
"""
    env = runtime_env(edition, enabled, multi_tenant)
    env["DJANGO_SETTINGS_MODULE"] = "apigateway.settings"
    for flag in ("MENU_ITEM_ESB_API", "MENU_ITEM_ESB_API_DOC", "SYNC_ESB_TO_APIGW_ENABLED"):
        env[f"FEATURE_FLAG_{flag}"] = flag_enabled
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=PROJECT, env=env, capture_output=True, text=True, check=False, timeout=60
    )
    assert result.returncode == 0, result.stderr
    state = json.loads(result.stdout.strip().splitlines()[-1])
    assert {key: state[key] for key in ("database", "app", "task", "routes")} == dict.fromkeys(
        ("database", "app", "task", "routes"), expected
    )
    assert state["flags"] == dict.fromkeys(
        ("MENU_ITEM_ESB_API", "MENU_ITEM_ESB_API_DOC", "SYNC_ESB_TO_APIGW_ENABLED"), flag_enabled == "true"
    )


@pytest.mark.parametrize(
    "esb_env", [{}, {"BK_ESB_DATABASE_PORT": "not-a-port", "BK_ESB_DATABASE_TLS_ENABLED": "true"}]
)
def test_disabled_esb_does_not_read_database_configuration(esb_env):
    env = {
        key: value
        for key, value in runtime_env("ee", "false", "false").items()
        if not key.startswith("BK_ESB_DATABASE_")
    }
    env.update(esb_env)
    result = subprocess.run(
        [sys.executable, "-c", "from apigateway.conf.default import DATABASES; assert 'bkcore' not in DATABASES"],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("script", ["on_migrate", "post_migrate"])
@pytest.mark.parametrize("edition, enabled, multi_tenant, expected", CASES)
def test_migration_scripts_dispatch_esb_commands(tmp_path, script, edition, enabled, multi_tenant, expected):
    # Stub manage.py side effects; scripts must evaluate the ESB policy in Bash.
    command_log = tmp_path / "commands.jsonl"
    python = tmp_path / "python"
    python.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "if sys.argv[1:2] == ['manage.py']:\n"
        "    with open(os.environ['COMMAND_LOG'], 'a') as stream:\n"
        "        stream.write(json.dumps(sys.argv[2:]) + '\\n')\n"
        "else:\n"
        "    raise SystemExit('unexpected Python invocation outside manage.py')\n"
    )
    python.chmod(0o755)
    env = runtime_env(edition, enabled, multi_tenant)
    env.update(PATH=f"{tmp_path}:{env['PATH']}", BK_HOME=str(tmp_path), COMMAND_LOG=str(command_log))
    result = subprocess.run(
        ["bash", str(DASHBOARD / "bin" / script)],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in command_log.read_text().splitlines()]
    if script == "on_migrate":
        assert ["migrate"] in commands
        assert ["register_to_bk_notice"] in commands
        assert (["migrate", "bkcore", "--database", "bkcore"] in commands) is expected
        assert (["create_esb_gateway"] in commands) is expected
        assert (["sync_esb_jwt_key_to_gateway"] in commands) is expected
    else:
        assert ["sync_global_resources"] in commands
        assert any("--gateway-name=bk-apigateway" in command for command in commands)
        assert any("--gateway-name=bk-esb" in command for command in commands) is expected
        assert (["sync_to_gateway_and_release"] in commands) is expected
