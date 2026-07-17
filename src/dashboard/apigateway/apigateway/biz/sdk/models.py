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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from django.conf import settings
from django.utils.timezone import now as timezone_now

from apigateway.apps.support.constants import ProgrammingLanguageEnum

if TYPE_CHECKING:
    from datetime import datetime

    from apigateway.apps.support.models import GatewaySDK


@dataclass
class SDKDocContext:
    gateway_name: str
    stage_name: str
    resource_name: str
    bk_api_url_tmpl: str
    sdk_created_time: datetime = field(default_factory=timezone_now)
    gateway_name_with_underscore: str = ""
    body_example: dict = field(default_factory=dict)
    path_params: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    install_command: str = ""
    artifact_url: str = ""
    package_name: str = ""

    def as_dict(self):
        return {
            "gateway_name": self.gateway_name,
            "gateway_name_with_underscore": self.gateway_name.replace("-", "_"),
            "stage_name": self.stage_name,
            "resource_name": self.resource_name,
            "sdk_created_time": self.sdk_created_time,
            "bk_api_url_tmpl": self.bk_api_url_tmpl,
            "body_example": self.body_example,
            "path_params": self.path_params,
            "query_params": self.query_params,
            "headers": self.headers,
            "install_command": self.install_command,
            "artifact_url": self.artifact_url,
            "package_name": self.package_name,
            "server_url": f"{self.bk_api_url_tmpl.replace('{api_name}', self.gateway_name).rstrip('/')}/{self.stage_name}",
        }


@dataclass
class DummySDKDocContext(SDKDocContext):
    gateway_name: str = "example"
    stage_name: str = "prod"
    resource_name: str = "get_example_status"
    bk_api_url_tmpl: str = field(default_factory=lambda: settings.BK_API_URL_TMPL)


@dataclass
class SDK:
    instance: GatewaySDK

    language = ProgrammingLanguageEnum.UNKNOWN

    @property
    def name(self):
        return self.instance.name

    @property
    def version(self):
        return self.instance.version_number

    @property
    def config(self):
        config = self.instance.config
        if not isinstance(config, dict):
            return {}
        if "artifacts" in config:
            return config
        legacy = config.get(self.language.value, {})
        return legacy if isinstance(legacy, dict) else {}

    @property
    def artifacts(self) -> list[dict[str, Any]]:
        artifacts = self.config.get("artifacts", [])
        return artifacts if isinstance(artifacts, list) else []

    @property
    def package_name(self) -> str:
        return self.config.get("package_name", self.name.replace("-", "_"))

    def find_artifact(self, *, distributor: str = "", artifact_type: str = "") -> dict[str, Any] | None:
        for artifact in self.artifacts:
            if distributor and artifact.get("distributor") != distributor:
                continue
            if artifact_type and artifact.get("type") != artifact_type:
                continue
            if artifact.get("filename") == "manifest.json":
                continue
            return artifact
        return None

    @property
    def install_command(self) -> str:
        artifact = self.find_artifact(distributor="bkrepo_generic")
        return f'curl -fLO "{artifact["url"]}"' if artifact and artifact.get("url") else ""

    @property
    def url(self):
        return self.instance.url

    @property
    def created_time(self):
        return self.instance.created_time

    @classmethod
    def from_model(cls, instance: GatewaySDK):
        return cls(instance=instance)

    def as_dict(self) -> dict[str, Any]:
        return {
            "language": self.language.value,
            "version": self.version,
            "url": self.url,
            "name": self.name,
            "install_command": self.install_command,
            "artifacts": self.artifacts,
            "package_name": self.package_name,
        }


@dataclass
class PythonSDK(SDK):
    language = ProgrammingLanguageEnum.PYTHON

    @property
    def sdk_name(self) -> str:
        return self.name

    @property
    def download_url(self) -> str:
        return self.instance.url

    @property
    def install_command(self) -> str:
        pypi = self.find_artifact(distributor="pypi")
        if pypi and pypi.get("coordinate"):
            return f'pip install "{pypi["coordinate"]}"'
        wheel = self.find_artifact(distributor="bkrepo_generic", artifact_type="wheel")
        return f'pip install "{wheel["url"]}"' if wheel and wheel.get("url") else ""

    @property
    def is_uploaded_to_pypi(self) -> bool:
        return self.find_artifact(distributor="pypi") is not None


@dataclass
class GoSDK(SDK):
    language = ProgrammingLanguageEnum.GO


@dataclass
class JavaSDK(SDK):
    language = ProgrammingLanguageEnum.JAVA

    @property
    def install_command(self) -> str:
        maven = self.find_artifact(distributor="maven")
        if maven and maven.get("coordinate"):
            return f'mvn dependency:get -Dartifact="{maven["coordinate"]}"'
        return super().install_command


@dataclass
class JavaScriptSDK(SDK):
    language = ProgrammingLanguageEnum.JAVASCRIPT

    @property
    def install_command(self) -> str:
        artifact = self.find_artifact(distributor="bkrepo_generic", artifact_type="npm_tgz")
        return f'npm install "{artifact["url"]}"' if artifact and artifact.get("url") else ""


@dataclass
class RustSDK(SDK):
    language = ProgrammingLanguageEnum.RUST


class SDKFactory:
    _mappings: ClassVar[dict[str, type[SDK]]] = {
        PythonSDK.language.value: PythonSDK,
        GoSDK.language.value: GoSDK,
        JavaSDK.language.value: JavaSDK,
        JavaScriptSDK.language.value: JavaScriptSDK,
        RustSDK.language.value: RustSDK,
    }

    @classmethod
    def create(cls, model: GatewaySDK) -> SDK:
        sdk_cls = cls._mappings.get(model.language, SDK)
        return sdk_cls.from_model(model)
