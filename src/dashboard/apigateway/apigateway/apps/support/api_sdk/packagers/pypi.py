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
from dataclasses import dataclass
from subprocess import check_output
from typing import List

from packaging.version import parse as parse_version

from apigateway.apps.support.api_sdk.models import Packager
from apigateway.apps.support.constants import ProgrammingLanguageEnum

logger = logging.getLogger(__name__)


@dataclass
class SourcePackager(Packager):
    def pack(self, output_dir: str) -> List[str]:
        self.context.config = {
            ProgrammingLanguageEnum.PYTHON.value: {
                "is_uploaded_to_pypi": False,
            }
        }

        check_output(
            [sys.executable, "setup.py", "sdist"],
            env={"HOME": output_dir},
            cwd=output_dir,
        )

        dist_path = os.path.join(
            output_dir, "dist", f"{self.context.name}-{parse_version(self.context.version)}.tar.gz"
        )

        return [dist_path]
