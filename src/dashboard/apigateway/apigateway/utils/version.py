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
from typing import List

from packaging import version
from packaging.version import Version, parse


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
    try:
        version = parse(current_version)
        return str(Version(f"{version.major}.{version.minor}.{version.micro + 1}"))
    except Exception:
        return ""


def parse_version(version: str) -> tuple[int, int, int, str | None]:
    """解析语义化版本字符串（如 1.2.3+prod），返回 (major, minor, patch, build_metadata)"""
    # 分离构建元数据
    version_part, *build_metadata_parts = version.split("+", maxsplit=1)
    build_metadata = build_metadata_parts[0] if build_metadata_parts else None

    # 解析主版本号
    version_numbers = version_part.split(".")
    major = _parse_version_part(version_numbers, 0)
    minor = _parse_version_part(version_numbers, 1)
    patch = _parse_version_part(version_numbers, 2)

    return major, minor, patch, build_metadata


def _parse_version_part(parts: list[str], index: int) -> int:
    """安全解析版本号的某一部分"""
    try:
        return int(parts[index])
    except (IndexError, ValueError):
        return 0


def get_nex_version_with_type(old_version: str, version_type: str) -> str:
    major, minor, patch, build_metadata = parse_version(old_version)
    if version_type == "major":
        major += 1
        minor, patch = 0, 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    else:
        raise ValueError("Invalid version type")
    new_version = f"{major}.{minor}.{patch}"
    if build_metadata:
        new_version += f"+{build_metadata}"
    return new_version


def is_version1_greater_than_version2(version1: str, version2: str) -> bool:
    try:
        return version.parse(version1) > version.parse(version2)
    except version.InvalidVersion:
        # fallback to str comp
        return version1 > version2
