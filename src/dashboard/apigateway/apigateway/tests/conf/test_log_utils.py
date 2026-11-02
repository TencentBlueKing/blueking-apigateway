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
import subprocess
import sys

import pytest

from apigateway.conf.log_utils import build_logging_config


def test_build_logging_config_uses_supported_pythonjsonlogger_formatter_path():
    config = build_logging_config("INFO", to_console=True, file_directory=None, file_format="json")

    assert config["formatters"]["verbose_json"]["()"] == "pythonjsonlogger.json.JsonFormatter"


@pytest.mark.parametrize("log_level", ["DEBUG", "INFO"])
def test_httpx2_request_logs_do_not_expose_credentials(log_level):
    # Apply the real logging configuration without changing pytest's own loggers.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import logging.config
import sys

import httpx2

from apigateway.conf.log_utils import build_logging_config

logging.config.dictConfig(build_logging_config(sys.argv[1], True, None, "json"))
transport = httpx2.MockTransport(lambda request: httpx2.Response(200))
with httpx2.Client(transport=transport) as client:
    response = client.get(
        "https://login.example.test/user/get_info/",
        params={"bk_ticket": "test-ticket-for-httpx2-logging"},
    )
    response.raise_for_status()
logging.getLogger("apigateway").info("business info remains visible")
logging.getLogger("httpx2").warning("httpx2 warning remains visible")
""",
            log_level,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout + result.stderr

    assert "test-ticket-for-httpx2-logging" not in output
    assert "HTTP Request:" not in output
    assert "business info remains visible" in output
    assert "httpx2 warning remains visible" in output
