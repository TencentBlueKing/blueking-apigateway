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
from apigateway.biz.sdk.process import build_subprocess_env, redact_sensitive_text


def test_build_subprocess_env_only_keeps_allowlisted_values(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("BKREPO_PASSWORD", "repository-secret")

    env = build_subprocess_env({"HOME": "/tmp/sdk-home"})

    assert env["PATH"] == "/usr/bin"
    assert env["HOME"] == "/tmp/sdk-home"
    assert "BKREPO_PASSWORD" not in env


def test_redact_sensitive_text_removes_labeled_and_url_credentials():
    value = "token=abc password=def secret=ghi https://user:pass@example.com/path"

    redacted = redact_sensitive_text(value)

    assert redacted == "token=*** password=*** secret=*** https://***@example.com/path"
