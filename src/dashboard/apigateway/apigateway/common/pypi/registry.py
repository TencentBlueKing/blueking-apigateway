# -*- coding: utf-8 -*-
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
from typing import Any

from packaging.version import InvalidVersion
from packaging.version import parse as parse_version
from pypi_simple import PyPISimple


class SimplePypiRegistry:
    def __init__(self, index_url: str, auth: Any = None):
        self.index_url = index_url
        self.auth = auth

    @property
    def _simple_client(self):
        return PyPISimple(self.index_url, self.auth)

    def _iter_packages(self, name: str, include_yanked: bool):
        with self._simple_client as client:
            page = client.get_project_page(name)

        if page is None:
            return

        for p in page.packages:
            if p.yanked and not include_yanked:
                continue

            if not p.version:
                continue

            version = None
            try:
                # bad version will be ignored
                version = parse_version(p.version)
            except InvalidVersion:
                pass

            yield version, p

    def search(self, name: str, version: str = "", package_type: str = ""):
        """查找满足指定规则的包"""

        target_version = None
        if version:
            # 此处必须转换，规则：https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
            target_version = parse_version(version)

        package = None
        last_version = None

        for v, p in self._iter_packages(name, False):
            if package_type and p.package_type != package_type:
                continue

            # skip
            if v is None:
                continue

            # 指定了版本号，说明只查询指定版本
            if v == target_version:
                return p

            if last_version is None or v > last_version:
                last_version = v
                package = p

        return None if target_version else package
