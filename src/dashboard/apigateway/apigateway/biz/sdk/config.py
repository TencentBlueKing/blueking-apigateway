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
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol

from django.conf import settings
from packaging.version import InvalidVersion, Version

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.constants import SEMVER_PATTERN

GENERATOR_PROPERTIES = {
    "python": ("packageName", "packageVersion", "projectName", "buildSystem"),
    "java": ("groupId", "artifactId", "artifactVersion", "invokerPackage", "apiPackage", "modelPackage", "library"),
    "go": ("packageName", "packageVersion", "withGoMod"),
    "javascript": ("projectName", "projectVersion", "moduleName", "usePromises"),
    "rust": ("packageName", "packageVersion", "library", "supportAsync"),
}

SUPPORTED_GENERATION_LANGUAGES = tuple(
    language.value
    for language in (
        ProgrammingLanguageEnum.PYTHON,
        ProgrammingLanguageEnum.JAVA,
        ProgrammingLanguageEnum.GO,
        ProgrammingLanguageEnum.JAVASCRIPT,
        ProgrammingLanguageEnum.RUST,
    )
)


class ResourceVersionLike(Protocol):
    version: str


@dataclass(frozen=True)
class SDKLanguageConfig:
    language: str
    generator_name: str
    project_name: str
    package_name: str
    package_version: str
    additional_properties: Mapping[str, str]
    native_distributor: str | None

    def __post_init__(self):
        allowed_properties = set(GENERATOR_PROPERTIES.get(self.language, ()))
        if set(self.additional_properties) != allowed_properties:
            raise ValueError(f"unsupported generator properties for {self.language}")
        object.__setattr__(self, "additional_properties", MappingProxyType(dict(self.additional_properties)))

    def build_fingerprint_payload(self) -> dict[str, object]:
        return {
            "language": self.language,
            "generator_name": self.generator_name,
            "project_name": self.project_name,
            "package_name": self.package_name,
            "package_version": self.package_version,
            "additional_properties": dict(self.additional_properties),
        }


@dataclass(frozen=True)
class BKRepoGenericConfig:
    endpoint_url: str
    username: str
    password: str = field(repr=False)
    project: str = ""
    bucket: str = ""


@dataclass(frozen=True)
class SDKGenerationConfig:
    enabled_languages: tuple[str, ...]
    queue: str
    generator_jar: str
    generator_version: str
    server_url_template: str
    generic_repository: BKRepoGenericConfig
    generic_retention_hours: int
    subprocess_timeout_seconds: int
    max_openapi_bytes: int
    max_output_bytes: int
    max_artifact_bytes: int
    max_log_bytes: int

    def for_resource_version(
        self, gateway_name: str, resource_version: ResourceVersionLike, language: str
    ) -> SDKLanguageConfig:
        return build_language_config(self, gateway_name, resource_version, language)


def get_sdk_generation_config() -> SDKGenerationConfig:
    config = settings.SDK_GENERATION
    enabled_languages = tuple(config["enabled_languages"])
    invalid_languages = set(enabled_languages).difference(SUPPORTED_GENERATION_LANGUAGES)
    if invalid_languages:
        raise ValueError(f"unsupported SDK generation languages: {sorted(invalid_languages)}")
    if len(enabled_languages) != len(set(enabled_languages)):
        raise ValueError("SDK generation languages must be unique")

    numeric_settings = (
        "generic_retention_hours",
        "subprocess_timeout_seconds",
        "max_openapi_bytes",
        "max_output_bytes",
        "max_artifact_bytes",
        "max_log_bytes",
    )
    if any(config[name] <= 0 for name in numeric_settings):
        raise ValueError("SDK generation limits must be positive")

    generic_repository = BKRepoGenericConfig(
        endpoint_url=settings.BKREPO_ENDPOINT_URL,
        username=settings.BKREPO_USERNAME,
        password=settings.BKREPO_PASSWORD,
        project=settings.BKREPO_PROJECT,
        bucket=settings.BKREPO_GENERIC_BUCKET,
    )
    if not all(
        (
            generic_repository.endpoint_url,
            generic_repository.username,
            generic_repository.password,
            generic_repository.project,
            generic_repository.bucket,
        )
    ):
        raise ValueError("BKRepo Generic configuration is required for SDK generation")

    return SDKGenerationConfig(
        enabled_languages=enabled_languages,
        generic_repository=generic_repository,
        **{
            name: config[name]
            for name in SDKGenerationConfig.__dataclass_fields__
            if name not in {"enabled_languages", "generic_repository"}
        },
    )


def normalize_gateway_name(gateway_name: str) -> str:
    return gateway_name.replace("-", "_")


def normalize_package_version(language: str, version: str) -> str:
    if language not in SUPPORTED_GENERATION_LANGUAGES:
        raise ValueError(f"unsupported SDK generation language: {language}")
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError("SDK package versions must follow Semantic Versioning")

    if language == ProgrammingLanguageEnum.PYTHON.value:
        try:
            return str(Version(version))
        except InvalidVersion as error:
            raise ValueError("SDK package version cannot be normalized as PEP 440") from error
    if language == ProgrammingLanguageEnum.GO.value:
        return f"v{version}"
    return version


def build_language_config(
    config: SDKGenerationConfig, gateway_name: str, resource_version: ResourceVersionLike, language: str
) -> SDKLanguageConfig:
    if language not in config.enabled_languages:
        raise ValueError(f"SDK language is not enabled: {language}")

    gateway_name_normalized = normalize_gateway_name(gateway_name)
    package_version = normalize_package_version(language, resource_version.version)
    template_values = {
        "gateway_name": gateway_name,
        "gateway_name_normalized": gateway_name_normalized,
    }

    if language == ProgrammingLanguageEnum.PYTHON.value:
        project_name = _format_template(settings.SDK_PYTHON_PROJECT_NAME_TEMPLATE, template_values)
        package_name = _format_template(settings.SDK_PYTHON_PACKAGE_NAME_TEMPLATE, template_values)
        return SDKLanguageConfig(
            language=language,
            generator_name=language,
            project_name=project_name,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "packageName": package_name,
                "packageVersion": package_version,
                "projectName": project_name,
                "buildSystem": "poetry",
            },
            native_distributor=_get_native_distributor(language),
        )

    if language == ProgrammingLanguageEnum.JAVA.value:
        artifact_id = _format_template(settings.SDK_JAVA_ARTIFACT_ID_TEMPLATE, template_values)
        package_name = _format_template(settings.SDK_JAVA_PACKAGE_TEMPLATE, template_values)
        return SDKLanguageConfig(
            language=language,
            generator_name=language,
            project_name=artifact_id,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "groupId": settings.SDK_JAVA_GROUP_ID,
                "artifactId": artifact_id,
                "artifactVersion": package_version,
                "invokerPackage": package_name,
                "apiPackage": f"{package_name}.api",
                "modelPackage": f"{package_name}.model",
                "library": "native",
            },
            native_distributor=_get_native_distributor(language),
        )

    if language == ProgrammingLanguageEnum.GO.value:
        project_name = f"{settings.SDK_GO_MODULE_PREFIX.rstrip('/')}/{gateway_name}"
        package_name = f"bkapi_{gateway_name_normalized}"
        return SDKLanguageConfig(
            language=language,
            generator_name=language,
            project_name=project_name,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "packageName": package_name,
                "packageVersion": package_version,
                "withGoMod": "true",
            },
            native_distributor=None,
        )

    if language == ProgrammingLanguageEnum.JAVASCRIPT.value:
        project_name = f"bkapi-{gateway_name}"
        package_name = f"{settings.SDK_JAVASCRIPT_PACKAGE_SCOPE}/bkapi-{gateway_name}"
        return SDKLanguageConfig(
            language=language,
            generator_name=language,
            project_name=project_name,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "projectName": project_name,
                "projectVersion": package_version,
                "moduleName": f"bkapi_{gateway_name_normalized}",
                "usePromises": "true",
            },
            native_distributor=None,
        )

    if language == ProgrammingLanguageEnum.RUST.value:
        package_name = _format_template(settings.SDK_RUST_CRATE_NAME_TEMPLATE, template_values)
        return SDKLanguageConfig(
            language=language,
            generator_name=language,
            project_name=package_name,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "packageName": package_name,
                "packageVersion": package_version,
                "library": "reqwest",
                "supportAsync": "true",
            },
            native_distributor=None,
        )

    raise ValueError(f"unsupported SDK generation language: {language}")


def _format_template(template: str, values: dict[str, str]) -> str:
    try:
        return template.format(**values)
    except (KeyError, ValueError) as error:
        raise ValueError(f"invalid SDK naming template: {template}") from error


def _get_native_distributor(language: str) -> str | None:
    if language == ProgrammingLanguageEnum.PYTHON.value:
        repository_url = settings.PYPI_MIRRORS_CONFIG.get("default", {}).get("repository_url", "")
        return "pypi" if repository_url else None
    if language == ProgrammingLanguageEnum.JAVA.value:
        repository_url = settings.MAVEN_MIRRORS_CONFIG.get("default", {}).get("repository_url", "")
        return "maven" if repository_url else None
    return None
