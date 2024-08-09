#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from typing import Any, ClassVar, Dict, List, Type

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.apps.support.models import GatewaySDK
from apigateway.common.pypi.pip import PipHelper
from apigateway.core.models import ResourceVersion
from apigateway.utils.pypi import RepositoryConfig


@dataclass
class SDKContext:
    name: str
    resource_version: ResourceVersion
    language: ProgrammingLanguageEnum
    version: str
    package: str = ""
    files: List[str] = field(default_factory=list)
    is_public: bool = False
    is_latest: bool = False
    is_distributed: bool = False
    url: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

    def update_language_config(self, to_updates: Dict[str, Any]):
        config = self.config.setdefault(self.language.value, {})
        config.update(to_updates)


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
        return self.instance.config.get(self.language.value, {})

    @property
    def install_command(self) -> str:
        return ""

    @property
    def url(self):
        return self.instance.url

    @property
    def created_time(self):
        return self.instance.created_time

    @classmethod
    def from_model(cls, instance: GatewaySDK):
        return cls(instance=instance)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language.value,
            "version": self.version,
            "url": self.url,
            "name": self.name,
            "install_command": self.install_command,
        }


@dataclass
class Generator:
    name: ClassVar[str] = ""

    context: SDKContext

    def generate(self, output_dir: str, resources: List[Dict[str, Any]]):
        raise NotImplementedError


@dataclass
class Packager:
    name: ClassVar[str] = ""
    context: SDKContext

    def pack(self, output_dir: str) -> List[str]:
        raise NotImplementedError


@dataclass
class DistributeResult:
    repository: str = ""
    is_local: bool = False
    filename: str = ""
    url: str = ""


@dataclass
class Distributor:
    """将生成的文件发布"""

    name: ClassVar[str] = ""

    context: SDKContext

    def distribute(self, output_dir: str, files: List[str]) -> DistributeResult:
        raise NotImplementedError


@dataclass
class SDKManager:
    name: str = ""
    is_public: bool = False

    def handle(self, output_dir: str, resource_version: ResourceVersion) -> SDKContext:
        raise NotImplementedError()


@dataclass
class PythonSDK(SDK):
    repository: str = ""
    index_url: str = ""
    repository_url: str = ""
    language = ProgrammingLanguageEnum.PYTHON

    def __post_init__(self):
        self.repository = self.config.get("repository", "")
        self._update_repository(self.repository)

    def _update_repository(self, repository):
        if not repository:
            return

        config = RepositoryConfig.by_name(repository)

        self.index_url = config.index_url
        self.repository_url = config.repository_url

    @property
    def sdk_name(self) -> str:
        return self.name

    @property
    def download_url(self) -> str:
        return self.instance.url

    @property
    def install_command(self) -> str:
        if not self.index_url:
            return ""

        helper = PipHelper(self.index_url)
        return helper.install_command(self.name, self.version)

    @property
    def is_uploaded_to_pypi(self) -> bool:
        return self.config.get("is_uploaded_to_pypi", False)


@dataclass
class GolangSDK(SDK):
    language = ProgrammingLanguageEnum.GOLANG


@dataclass
class JavaSDK(SDK):
    language = ProgrammingLanguageEnum.JAVA


class SDKFactory:
    _mappings: Dict[str, Type[SDK]] = {
        PythonSDK.language.value: PythonSDK,
        GolangSDK.language.value: GolangSDK,
        JavaSDK.language.value: JavaSDK,
    }

    @classmethod
    def create(cls, model: GatewaySDK) -> SDK:
        sdk_cls = cls._mappings.get(model.language, SDK)
        return sdk_cls.from_model(model)
