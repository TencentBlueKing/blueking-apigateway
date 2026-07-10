# -*- coding: utf-8 -*-
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
import pytest
from django.conf import settings
from django.test import override_settings

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.sdk.config import (
    SDKLanguageConfig,
    get_sdk_generation_config,
    normalize_gateway_name,
    normalize_package_version,
)

EXPECTED_GENERATOR_PROPERTIES = {
    "python": {"packageName", "packageVersion", "projectName", "buildSystem"},
    "java": {"groupId", "artifactId", "artifactVersion", "invokerPackage", "apiPackage", "modelPackage", "library"},
    "go": {"packageName", "packageVersion", "withGoMod"},
    "javascript": {"projectName", "projectVersion", "moduleName", "usePromises"},
    "rust": {"packageName", "packageVersion", "library", "supportAsync"},
}


@pytest.fixture(autouse=True)
def configure_bkrepo_generic(settings):
    settings.BKREPO_ENDPOINT_URL = "https://bkrepo.example.com"
    settings.BKREPO_USERNAME = "sdk-user"
    settings.BKREPO_PASSWORD = "sdk-password"
    settings.BKREPO_PROJECT = "sdk-project"
    settings.BKREPO_GENERIC_BUCKET = "sdk-generic"


def test_programming_languages_are_the_new_supported_set():
    assert [value for value, _label in ProgrammingLanguageEnum.get_choices()] == [
        "unknown",
        "python",
        "java",
        "go",
        "javascript",
        "rust",
    ]


def test_sdk_generation_config_uses_the_default_server_template():
    config = get_sdk_generation_config()

    assert config.enabled_languages == ("python", "java", "go", "javascript", "rust")
    assert config.server_url_template == settings.SDK_GENERATION["server_url_template"]


def test_sdk_generation_config_requires_bkrepo_generic_for_deployment():
    config = get_sdk_generation_config()

    assert config.generic_repository.endpoint_url == "https://bkrepo.example.com"
    assert config.generic_repository.username == "sdk-user"
    assert config.generic_repository.password == "sdk-password"
    assert config.generic_repository.project == "sdk-project"
    assert config.generic_repository.bucket == "sdk-generic"


@pytest.mark.parametrize(
    "setting_name",
    [
        "BKREPO_ENDPOINT_URL",
        "BKREPO_USERNAME",
        "BKREPO_PASSWORD",
        "BKREPO_PROJECT",
        "BKREPO_GENERIC_BUCKET",
    ],
)
def test_sdk_generation_config_rejects_incomplete_bkrepo_generic(settings, setting_name):
    setattr(settings, setting_name, "")

    with pytest.raises(ValueError, match="BKRepo Generic"):
        get_sdk_generation_config()


@override_settings(
    SDK_PYTHON_PROJECT_NAME_TEMPLATE="custom-{gateway_name}",
    SDK_PYTHON_PACKAGE_NAME_TEMPLATE="custom_{gateway_name_normalized}",
    SDK_JAVA_GROUP_ID="com.example.sdk",
    SDK_JAVA_ARTIFACT_ID_TEMPLATE="client-{gateway_name}",
    SDK_JAVA_PACKAGE_TEMPLATE="com.example.{gateway_name_normalized}",
    SDK_GO_MODULE_PREFIX="git.example.com/sdk",
    SDK_JAVASCRIPT_PACKAGE_SCOPE="@example",
    SDK_RUST_CRATE_NAME_TEMPLATE="client_{gateway_name_normalized}",
)
def test_sdk_generation_config_uses_configurable_language_names():
    config = get_sdk_generation_config()

    python_config = config.for_resource_version("my-gateway", "1.2.3", "python")
    java_config = config.for_resource_version("my-gateway", "1.2.3", "java")
    go_config = config.for_resource_version("my-gateway", "1.2.3", "go")
    javascript_config = config.for_resource_version("my-gateway", "1.2.3", "javascript")
    rust_config = config.for_resource_version("my-gateway", "1.2.3", "rust")

    assert python_config.project_name == "custom-my-gateway"
    assert python_config.package_name == "custom_my_gateway"
    assert java_config.package_name == "com.example.my_gateway"
    assert java_config.additional_properties["artifactId"] == "client-my-gateway"
    assert go_config.project_name == "git.example.com/sdk/my-gateway"
    assert javascript_config.package_name == "@example/bkapi-my-gateway"
    assert rust_config.package_name == "client_my_gateway"


@override_settings(
    PYPI_MIRRORS_CONFIG={"default": {"repository_url": "https://pypi.example.com"}},
    MAVEN_MIRRORS_CONFIG={"default": {"repository_url": "https://maven.example.com"}},
)
def test_sdk_generation_config_detects_optional_native_distributors():
    config = get_sdk_generation_config()

    assert config.for_resource_version("my-gateway", "1.2.3", "python").native_distributor == "pypi"
    assert config.for_resource_version("my-gateway", "1.2.3", "java").native_distributor == "maven"
    assert config.for_resource_version("my-gateway", "1.2.3", "go").native_distributor is None


def test_sdk_generation_config_keeps_native_distributors_optional():
    config = get_sdk_generation_config()

    assert config.for_resource_version("my-gateway", "1.2.3", "python").native_distributor is None
    assert config.for_resource_version("my-gateway", "1.2.3", "java").native_distributor is None


@pytest.mark.parametrize("language", ["python", "java", "go", "javascript", "rust"])
def test_sdk_generation_config_uses_only_supported_generator_properties(language):
    config = get_sdk_generation_config()

    language_config = config.for_resource_version("my-gateway", "1.2.3", language)

    assert set(language_config.additional_properties) == EXPECTED_GENERATOR_PROPERTIES[language]


def test_sdk_language_config_rejects_unsupported_generator_properties():
    with pytest.raises(ValueError, match="unsupported generator properties"):
        SDKLanguageConfig(
            language="python",
            generator_name="python",
            project_name="bkapi-my-gateway",
            package_name="bkapi_my_gateway",
            package_version="1.2.3",
            additional_properties={"unsupportedProperty": "true"},
            native_distributor=None,
        )


def test_sdk_language_fingerprint_excludes_bkrepo_credentials():
    config = get_sdk_generation_config()

    fingerprint = config.for_resource_version("my-gateway", "1.2.3", "python").build_fingerprint_payload()

    assert "sdk-user" not in str(fingerprint)
    assert "sdk-password" not in str(fingerprint)


def test_normalize_gateway_name_replaces_hyphens_with_underscores():
    assert normalize_gateway_name("my-gateway") == "my_gateway"


def test_package_versions_are_derived_from_resource_version():
    assert normalize_package_version("python", "1.2.3-beta.1") == "1.2.3b1"
    assert normalize_package_version("go", "1.2.3") == "v1.2.3"
    assert normalize_package_version("java", "1.2.3") == "1.2.3"


def test_package_version_rejects_non_semver_versions():
    with pytest.raises(ValueError, match="Semantic Versioning"):
        normalize_package_version("python", "2026.07")


def test_package_version_rejects_the_legacy_golang_alias():
    with pytest.raises(ValueError, match="unsupported SDK generation language"):
        normalize_package_version("golang", "1.2.3")
