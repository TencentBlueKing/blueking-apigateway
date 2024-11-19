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
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from apigateway.apps.support.api_sdk.models import Packager

logger = logging.getLogger(__name__)


@dataclass
class SourcePackager(Packager):
    def pack(self, output_dir: str) -> List[str]:
        # 保存当前工作目录
        original_dir = os.getcwd()
        try:
            # 切换到 Maven 项目目录
            os.chdir(output_dir)
            result = subprocess.run(
                [
                    "mvn",
                    "-s",
                    str(Path(original_dir) / "apigateway/apps/support/api_sdk/maven/settings.xml"),
                    "clean",
                    "package",
                ],
                env={"HOME": output_dir},
                cwd=output_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )

            logger.info("stdout %s", result.stdout)
            logger.info("stderr %s", result.stderr)
            # 查找生成的 JAR 文件
            target_dir = os.path.join(output_dir, "target")
            jar_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".jar")]

            if not jar_files:
                raise FileNotFoundError("No JAR files found in the target directory.")

            return [os.path.join(output_dir + "/target", os.path.basename(jar_file)) for jar_file in jar_files]

        except subprocess.CalledProcessError as e:
            logger.exception("Command failed with return code %s", e.returncode)
            raise
        finally:
            # 切换回原来的工作目录
            os.chdir(original_dir)
