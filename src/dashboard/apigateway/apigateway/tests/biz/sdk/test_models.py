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
from types import SimpleNamespace

import pytest

from apigateway.biz.sdk import SDKDocContext, SDKFactory
from apigateway.biz.sdk.models import SDK, GoSDK, JavaScriptSDK, JavaSDK, PythonSDK, RustSDK
from apigateway.utils.time import now_datetime


class TestSDKDocContext:
    def test_as_dict(self):
        now = now_datetime()
        context = SDKDocContext(
            gateway_name="foo-bar",
            stage_name="prod",
            resource_name="get_color",
            bk_api_url_tmpl="http://{api_name}.example.com",
            sdk_created_time=now,
        )
        result = context.as_dict()

        assert result["sdk_created_time"] == now
        assert result["gateway_name_with_underscore"] == "foo_bar"


@pytest.mark.parametrize(
    ("language", "sdk_type", "artifact_type", "command"),
    [
        ("python", PythonSDK, "wheel", "pip install"),
        ("java", JavaSDK, "distribution_zip", "curl -fLO"),
        ("go", GoSDK, "go_zip", "curl -fLO"),
        ("javascript", JavaScriptSDK, "npm_tgz", "npm install"),
        ("rust", RustSDK, "crate", "curl -fLO"),
    ],
)
def test_sdk_factory_uses_completed_generic_artifacts(language, sdk_type, artifact_type, command):
    sdk = SDKFactory.create(
        SimpleNamespace(
            language=language,
            config={
                "package_name": "bkapi_demo",
                "artifacts": [
                    {
                        "distributor": "bkrepo_generic",
                        "type": artifact_type,
                        "filename": "sdk-package",
                        "url": "https://repo.example.com/sdk-package",
                    }
                ],
            },
            name="bkapi-my-gateway",
            version_number="1.2.3",
            url="https://repo.example.com/sdk-package",
        )
    )

    assert isinstance(sdk, sdk_type)
    assert sdk.as_dict()["language"] == language
    assert sdk.package_name == "bkapi_demo"
    assert sdk.install_command.startswith(command)


def test_sdk_factory_does_not_map_legacy_golang_value():
    sdk = SDKFactory.create(
        SimpleNamespace(language="golang", config={}, name="legacy", version_number="1.0.0", url="")
    )

    assert type(sdk) is SDK
    assert sdk.as_dict()["language"] == "unknown"


def test_native_repository_coordinates_are_preferred():
    python = SDKFactory.create(
        SimpleNamespace(
            language="python",
            config={
                "artifacts": [
                    {
                        "distributor": "pypi",
                        "type": "wheel",
                        "filename": "sdk.whl",
                        "url": "https://pypi.example.com/sdk.whl",
                        "coordinate": "bkapi-demo==1.2.3",
                    }
                ]
            },
            name="bkapi-demo",
            version_number="1.2.3",
            url="",
        )
    )
    java = SDKFactory.create(
        SimpleNamespace(
            language="java",
            config={
                "artifacts": [
                    {
                        "distributor": "maven",
                        "type": "jar",
                        "filename": "sdk.jar",
                        "url": "https://maven.example.com/sdk.jar",
                        "coordinate": "com.example:bkapi-demo:1.2.3",
                    }
                ]
            },
            name="bkapi-demo",
            version_number="1.2.3",
            url="",
        )
    )

    assert python.install_command == 'pip install "bkapi-demo==1.2.3"'
    assert java.install_command == 'mvn dependency:get -Dartifact="com.example:bkapi-demo:1.2.3"'
