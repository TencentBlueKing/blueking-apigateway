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
import re
from typing import List

from packaging import version


def _filter_the_valid_versions(versions: List[str]) -> List[str]:
    data = []
    for v in versions:
        try:
            version.parse(v)
            data.append(v)
        except version.InvalidVersion:
            pass

    return data


def max_version(versions: List[str]) -> str:
    if len(versions) == 0:
        return ""
    if len(versions) == 1:
        return versions[0]

    try:
        return max(versions, key=version.parse)
    except version.InvalidVersion:
        # some version_str in version maybe invalid
        valid_versions = _filter_the_valid_versions(versions)
        if valid_versions:
            return max(valid_versions, key=version.parse)

        # use the string comp
        return max(versions)


def get_next_version(current_version: str) -> str:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.+-]+))?(?:\+([a-zA-Z0-9.+-]+))?$", current_version)
    if not match:
        return "0.0.1"

        # 提取主版本号、次版本号和补丁版本号
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    pre_release = match.group(4)  # 预发布标签
    build_metadata = match.group(5)  # 构建元数据

    # 根据不同的类型增加版本号
    patch += 1

    # 构造新的版本号字符串，并保留后缀（如果需要）
    new_version = f"{major}.{minor}.{patch}"
    if pre_release:
        new_version += f"-{pre_release}"
    if build_metadata:
        new_version += f"+{build_metadata}"
    return new_version


def is_version1_greater_than_version2(version1: str, version2: str) -> bool:
    try:
        return version.parse(version1) > version.parse(version2)
    except version.InvalidVersion:
        # fallback to str comp
        return version1 > version2
