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
from dataclasses import dataclass
from pathlib import Path
from typing import List

from packaging.version import parse as parse_version

from apigateway.apps.support.api_sdk.models import Packager
from apigateway.utils.archivefile import TgzArchiveFile
from apigateway.utils.file import iter_files_recursive

logger = logging.getLogger(__name__)


@dataclass
class TgzPackager(Packager):
    def pack(self, output_dir: str) -> List[str]:
        output = Path(output_dir)
        archive = TgzArchiveFile()
        files = [f.relative_to(output).as_posix() for f in iter_files_recursive(output)]

        return [
            archive.archive(output_dir, f"{self.context.name}-{parse_version(self.context.version)}.tar.gz", files)
        ]
