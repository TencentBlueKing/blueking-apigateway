#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import ClassVar, List

from apigateway.apps.support.api_sdk.exceptions import DistributeError
from apigateway.apps.support.api_sdk.models import DistributeResult, Distributor
from apigateway.utils.maven import RepositoryConfig

logger = logging.getLogger(__name__)


@dataclass
class MavenSourceDistributor(Distributor):
    repository: ClassVar[str] = "default"
    group_id: ClassVar[str] = "com.tencent.bkapi"
    repository_config: RepositoryConfig = field(init=False)

    def __post_init__(self):
        self.repository_config = RepositoryConfig.by_name(self.repository)

    def get_download_url(self):
        group_path = self.group_id.replace(".", "/")
        artifact_id = self.context.package
        version = self.context.version
        repository_url = self.repository_config.repository_url
        return f"{repository_url}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.jar"

    def distribute(self, output_dir: str, files: List[str]) -> DistributeResult:
        result = DistributeResult(repository=self.repository, is_local=True)

        if not files:
            return result

        if not self.repository_config.repository_url:
            raise DistributeError(f"maven repository [{self.repository}] configuration is not set")

        self.context.update_language_config(
            {
                "is_uploaded_to_maven": True,
                "repository": self.repository_config.repository_url,
            }
        )

        source_dir = output_dir
        env = os.environ.copy()
        env["HOME"] = source_dir

        command = [
            "mvn",
            "-s",
            os.path.join(os.getcwd(), "apigateway/apps/support/api_sdk/maven/settings.xml"),
            "-e",
            "deploy:deploy-file",
            "-DgroupId=" + self.group_id,
            "-DartifactId=" + self.context.package,
            "-Dversion=" + self.context.version,
            "-Dpackaging=jar",
            "-Dfile=" + files[0],
            "-DrepositoryId=bkapi",
            "-Durl=" + self.repository_config.repository_url,
            "-Dusername=" + self.repository_config.username,
            "-Dpassword=" + self.repository_config.password,
        ]

        try:
            completed_process = subprocess.run(
                command,
                env=env,
                cwd=source_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,  # Python 3.7+，将输出解码为字符串
            )
            print("stdout:", completed_process.stdout)
            print("stderr:", completed_process.stderr)
            completed_process.check_returncode()  # 检查命令是否成功
        except subprocess.CalledProcessError:
            logger.exception("upload to maven repository [%s] failed", self.repository)
            raise DistributeError(f"can not distribute to maven repository [{self.repository}]")

        result.url = self.get_download_url()
        result.is_local = result.url == ""

        return result
