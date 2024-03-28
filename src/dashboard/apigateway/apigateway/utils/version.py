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

from apigateway.utils import time


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
        std_version = version.parse(current_version)
        return f"{std_version.major}.{std_version.minor}.{std_version.micro + 1}"
    except version.InvalidVersion:
        now = time.now_datetime()
        now_str = time.format(now, fmt="YYYYMMDDHHmmss")
        return current_version + f".{now_str}"


def is_version1_greater_than_version2(version1: str, version2: str) -> bool:
    try:
        return version.parse(version1) > version.parse(version2)
    except version.InvalidVersion:
        # fallback to str comp
        return version1 > version2
