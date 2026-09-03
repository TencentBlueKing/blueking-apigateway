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
from ddf import G

from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk import SDKDocContext, SDKFactory
from apigateway.biz.sdk.models import SDK, GoSDK, JavaScriptSDK, JavaSDK, PythonSDK
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


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


def test_python_legacy_repository_config_keeps_install_command(settings):
    settings.PYPI_MIRRORS_CONFIG = {"default": {"index_url": "https://repo.example.com/simple"}}
    sdk = SDKFactory.create(
        SimpleNamespace(
            language="python",
            config={"python": {"repository": "default", "is_uploaded_to_pypi": True}},
            name="bkapi-demo",
            version_number="1.2.3",
            url="",
        )
    )

    assert sdk.install_command == "pip install --extra-index-url=https://repo.example.com/simple bkapi-demo==1.2.3"


def test_go_install_command_selects_module_zip():
    sdk = SDKFactory.create(
        SimpleNamespace(
            language="go",
            config={
                "artifacts": [
                    {
                        "distributor": "bkrepo_generic",
                        "type": "go_info",
                        "filename": "v1.2.3.info",
                        "url": "https://repo/v1.2.3.info",
                    },
                    {
                        "distributor": "bkrepo_generic",
                        "type": "go_mod",
                        "filename": "v1.2.3.mod",
                        "url": "https://repo/v1.2.3.mod",
                    },
                    {
                        "distributor": "bkrepo_generic",
                        "type": "go_zip",
                        "filename": "v1.2.3.zip",
                        "url": "https://repo/v1.2.3.zip",
                    },
                ]
            },
            name="bkapi-demo",
            version_number="1.2.3",
            url="https://repo/v1.2.3.info",
        )
    )

    assert sdk.install_command == 'curl -fLO "https://repo/v1.2.3.zip"'


def test_sdk_factory_reads_generated_state_from_explicit_item_relation(fake_gateway, fake_resource_version):
    gateway_sdk = G(
        GatewaySDK,
        gateway=fake_gateway,
        resource_version=fake_resource_version,
        language="javascript",
        version_number=fake_resource_version.version,
        name="@bkapi/openapi-demo",
        url="https://legacy/fallback.tgz",
        _config="{}",
    )
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    item = G(
        SDKGenerationItem,
        task=task,
        language="javascript",
        gateway_sdk=gateway_sdk,
        config_snapshot={"package_name": "@bkapi/openapi-demo"},
    )
    G(
        SDKArtifact,
        item=item,
        distributor="bkrepo_generic",
        artifact_type="npm_tgz",
        filename="bkapi-openapi-demo-1.2.3.tgz",
        url="https://repo/sdk.tgz",
        status="success",
    )

    sdk = SDKFactory.create(gateway_sdk)

    assert sdk.artifacts[0]["type"] == "npm_tgz"
    assert sdk.url == "https://repo/sdk.tgz"
    assert sdk.install_command == 'npm install "https://repo/sdk.tgz"'
    assert sdk.package_name == "@bkapi/openapi-demo"


def test_sdk_factory_legacy_row_without_relation_keeps_config_fallback():
    sdk = SDKFactory.create(
        SimpleNamespace(
            language="javascript",
            config={"javascript": {"package_name": "legacy-js"}},
            name="legacy",
            version_number="1.0.0",
            url="https://legacy/sdk.tgz",
        )
    )

    assert sdk.package_name == "legacy-js"
    assert sdk.url == "https://legacy/sdk.tgz"
