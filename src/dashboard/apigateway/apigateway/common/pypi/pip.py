# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from urllib.parse import urlparse

from packaging.version import InvalidVersion
from packaging.version import parse as parse_version


class PipHelper:
    def __init__(self, extra_index_url: str = ""):
        self.extra_index_url = extra_index_url

    def install_command(self, package: str, version: str = ""):
        commands = ["pip", "install"]

        if self.extra_index_url:
            commands.append(f"--extra-index-url={self.extra_index_url}")

            urlinfo = urlparse(self.extra_index_url)
            if urlinfo.scheme == "http":
                commands.append(f"--trusted-host={urlinfo.hostname}")

        if version:
            _version = version
            try:
                _version = parse_version(version)
            except InvalidVersion:
                pass

            commands.append(f"{package}=={_version}")
        else:
            commands.append(f"{package}")

        return " ".join(commands)
