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
import logging
import os
import sys
from dataclasses import dataclass, field
from subprocess import CalledProcessError, check_call
from typing import ClassVar, List, Optional

from apigateway.apps.support.api_sdk.constants import PYPIRC_TMPL
from apigateway.apps.support.api_sdk.exceptions import DistributeError
from apigateway.apps.support.api_sdk.models import DistributeResult, Distributor
from apigateway.common.pypi.registry import SimplePypiRegistry
from apigateway.utils.file import write_to_file
from apigateway.utils.pypi import RepositoryConfig

logger = logging.getLogger(__name__)


@dataclass
class PypiSourceDistributor(Distributor):
    repository: ClassVar[str] = "default"
    package_searcher: Optional[SimplePypiRegistry] = None
    repository_config: RepositoryConfig = field(init=False)

    def __post_init__(self):
        self.repository_config = RepositoryConfig.by_name(self.repository)

        if self.repository_config.index_url:
            self.package_searcher = SimplePypiRegistry(self.repository_config.index_url)

    def _setup_pypirc(self, home_dir: str):
        config = self.repository_config

        pypirc_content = PYPIRC_TMPL.format(
            index_server=self.repository,
            repository=config.repository_url,
            username=config.username,
            password=config.password,
        )
        write_to_file(pypirc_content, os.path.join(home_dir, ".pypirc"))

    def get_download_url(self):
        if not self.package_searcher:
            return ""

        result = self.package_searcher.search(self.context.name, self.context.version)
        if not result:
            return ""

        return result.url

    def distribute(self, output_dir: str, files: List[str]) -> DistributeResult:
        result = DistributeResult(repository=self.repository, is_local=True)

        if not files:
            return result

        if not self.repository_config.repository_url:
            raise DistributeError(f"pypi repository [{self.repository}] configuration is not set")

        self.context.update_language_config(
            {
                "is_uploaded_to_pypi": True,
                "repository": self.repository,
            }
        )

        source_dir = output_dir
        self._setup_pypirc(source_dir)

        env = os.environ.copy()
        env["HOME"] = source_dir

        try:
            check_call(
                [sys.executable, "setup.py", "sdist", "upload", "-r", self.repository],
                env=env,
                cwd=source_dir,
            )
        except CalledProcessError:
            logger.exception("upload to pypi repository [%s] failed", self.repository)
            raise DistributeError(f"can not distribute to pypi repository [{self.repository}]")

        result.url = self.get_download_url()
        result.is_local = result.url == ""

        return result
