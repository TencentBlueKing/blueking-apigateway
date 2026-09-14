#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
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
from __future__ import annotations

import os
import re

SAFE_ENVIRONMENT_VARIABLES = {
    "HOME",
    "PATH",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "JAVA_HOME",
    "MAVEN_HOME",
    "GOPATH",
    "GOCACHE",
    "GOMODCACHE",
    "NPM_CONFIG_CACHE",
    "UV_CACHE_DIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "no_proxy",
}


def build_subprocess_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = {name: value for name, value in os.environ.items() if name in SAFE_ENVIRONMENT_VARIABLES}
    if overrides:
        env.update(overrides)
    return env


def redact_sensitive_text(value: str, sensitive_values: tuple[str, ...] = ()) -> str:
    for sensitive in sensitive_values:
        if sensitive:
            value = value.replace(sensitive, "***")
    value = re.sub(r"(?i)(authorization\s*:\s*)[^\s]+(?:\s+[^\s]+)?", r"\1***", value)
    value = re.sub(r"(?i)((?:secret|token|password)\s*[=:]\s*)[^\s&]+", r"\1***", value)
    return re.sub(r"(https?://)[^/@\s]+@", r"\1***@", value)
