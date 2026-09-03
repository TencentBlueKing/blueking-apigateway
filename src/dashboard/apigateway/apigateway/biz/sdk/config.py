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

from apigateway.biz.constants import SEMVER_PATTERN
from apigateway.biz.sdk.exceptions import SDKRepoConfigError

GENERATOR_PROPERTIES = {
    "python": ("packageName", "packageVersion", "projectName", "buildSystem", "hideGenerationTimestamp"),
    "java": (
        "groupId",
        "artifactId",
        "artifactVersion",
        "invokerPackage",
        "apiPackage",
        "modelPackage",
        "library",
        "hideGenerationTimestamp",
    ),
    "go": ("packageName", "packageVersion", "withGoMod", "hideGenerationTimestamp"),
    "javascript": ("npmName", "npmVersion", "supportsES6", "hideGenerationTimestamp"),
}

SUPPORTED_GENERATION_LANGUAGES = ("python", "java", "go", "javascript")


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
        additional_properties = dict(self.additional_properties)
        additional_properties["hideGenerationTimestamp"] = "true"
        allowed_properties = set(GENERATOR_PROPERTIES.get(self.language, ()))
        if set(additional_properties) != allowed_properties:
            raise ValueError(f"unsupported generator properties for {self.language}")
        object.__setattr__(self, "additional_properties", MappingProxyType(additional_properties))

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
class SDKGenerationPolicy:
    enabled: bool
    languages: tuple[str, ...]
    queue: str
    retry_delays: tuple[int, int]
    python_distribution_prefix: str
    java_group_id: str
    java_package_prefix: str
    go_module_prefix: str
    javascript_package_scope: str

    def for_resource_version(
        self, gateway_name: str, resource_version: ResourceVersionLike, language: str
    ) -> SDKLanguageConfig:
        return build_language_config(self, gateway_name, resource_version, language)


@dataclass(frozen=True)
class SDKWorkerConfig:
    policy: SDKGenerationPolicy
    generator_jar: str
    generator_version: str
    worker_lock_file: str
    server_url_template: str
    generic_repository: BKRepoGenericConfig
    generic_retention_hours: int
    subprocess_timeout_seconds: int
    max_openapi_bytes: int
    max_output_bytes: int
    max_artifact_bytes: int

    @property
    def enabled_languages(self) -> tuple[str, ...]:
        return self.policy.languages

    @property
    def queue(self) -> str:
        return self.policy.queue

    def for_resource_version(
        self, gateway_name: str, resource_version: ResourceVersionLike, language: str
    ) -> SDKLanguageConfig:
        return self.policy.for_resource_version(gateway_name, resource_version, language)


def get_sdk_generation_policy() -> SDKGenerationPolicy:
    config = settings.SDK_GENERATION
    languages = tuple(settings.BK_SDK_LANGUAGES)
    invalid_languages = set(languages).difference(SUPPORTED_GENERATION_LANGUAGES)
    if invalid_languages:
        raise SDKRepoConfigError(f"unsupported SDK generation languages: {sorted(invalid_languages)}")
    if len(languages) != len(set(languages)):
        raise SDKRepoConfigError("SDK generation languages must be unique")

    retry_delays = tuple(settings.SDK_GENERATION_RETRY_DELAYS)
    if len(retry_delays) != 2 or any(delay <= 0 for delay in retry_delays):
        raise SDKRepoConfigError("SDK generation retry delays must contain two positive values")

    return SDKGenerationPolicy(
        enabled=settings.SDK_GENERATION_ENABLED,
        languages=languages,
        queue=config["queue"],
        retry_delays=retry_delays,
        python_distribution_prefix=settings.SDK_PYTHON_DISTRIBUTION_PREFIX,
        java_group_id=settings.SDK_JAVA_GROUP_ID,
        java_package_prefix=settings.SDK_JAVA_PACKAGE_PREFIX,
        go_module_prefix=settings.SDK_GO_MODULE_PREFIX,
        javascript_package_scope=settings.SDK_JAVASCRIPT_PACKAGE_SCOPE,
    )


def get_sdk_worker_config() -> SDKWorkerConfig:
    config = settings.SDK_GENERATION
    policy = get_sdk_generation_policy()

    numeric_settings = (
        "generic_retention_hours",
        "subprocess_timeout_seconds",
        "max_openapi_bytes",
        "max_output_bytes",
        "max_artifact_bytes",
    )
    if any(config[name] <= 0 for name in numeric_settings):
        raise SDKRepoConfigError("SDK generation limits must be positive")

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
        raise SDKRepoConfigError("BKRepo Generic configuration is required for SDK generation")

    return SDKWorkerConfig(
        policy=policy,
        generic_repository=generic_repository,
        **{
            name: config[name]
            for name in SDKWorkerConfig.__dataclass_fields__
            if name not in {"policy", "generic_repository"}
        },
    )


def get_sdk_generation_config() -> SDKWorkerConfig:
    """Compatibility entrypoint for worker call sites migrated in later tasks."""
    return get_sdk_worker_config()


def normalize_gateway_name(gateway_name: str) -> str:
    return gateway_name.replace("-", "_")


def normalize_package_version(language: str, version: str) -> str:
    if language not in SUPPORTED_GENERATION_LANGUAGES:
        raise ValueError(f"unsupported SDK generation language: {language}")
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError("SDK package versions must follow Semantic Versioning")

    if language == "python":
        try:
            return str(Version(version))
        except InvalidVersion as error:
            raise ValueError("SDK package version cannot be normalized as PEP 440") from error
    if language == "go":
        return f"v{version}"
    return version


def build_language_config(
    policy: SDKGenerationPolicy, gateway_name: str, resource_version: ResourceVersionLike, language: str
) -> SDKLanguageConfig:
    if language not in policy.languages:
        raise ValueError(f"SDK language is not enabled: {language}")

    gateway_name_normalized = normalize_gateway_name(gateway_name)
    package_version = normalize_package_version(language, resource_version.version)

    if language == "python":
        project_name = f"{policy.python_distribution_prefix}-{gateway_name}"
        package_name = normalize_gateway_name(project_name)
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

    if language == "java":
        artifact_id = f"bkapi-openapi-{gateway_name}"
        package_name = f"{policy.java_package_prefix}.{gateway_name_normalized}"
        return SDKLanguageConfig(
            language=language,
            generator_name=language,
            project_name=artifact_id,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "groupId": policy.java_group_id,
                "artifactId": artifact_id,
                "artifactVersion": package_version,
                "invokerPackage": package_name,
                "apiPackage": f"{package_name}.api",
                "modelPackage": f"{package_name}.model",
                "library": "native",
            },
            native_distributor=_get_native_distributor(language),
        )

    if language == "go":
        project_name = f"{policy.go_module_prefix}/openapi/{gateway_name}"
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

    if language == "javascript":
        package_name = f"{policy.javascript_package_scope}/openapi-{gateway_name}"
        return SDKLanguageConfig(
            language=language,
            generator_name="typescript-fetch",
            project_name=package_name,
            package_name=package_name,
            package_version=package_version,
            additional_properties={
                "npmName": package_name,
                "npmVersion": package_version,
                "supportsES6": "true",
            },
            native_distributor=None,
        )

    raise ValueError(f"unsupported SDK generation language: {language}")


def _get_native_distributor(language: str) -> str | None:
    if language == "python":
        repository_url = settings.PYPI_MIRRORS_CONFIG.get("default", {}).get("repository_url", "")
        return "pypi" if repository_url else None
    if language == "java":
        repository_url = settings.MAVEN_MIRRORS_CONFIG.get("default", {}).get("repository_url", "")
        return "maven" if repository_url else None
    return None
