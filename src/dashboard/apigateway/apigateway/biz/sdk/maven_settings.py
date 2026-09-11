#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
# Copyright (C) Tencent. All rights reserved.
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
from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.utils.maven import RepositoryConfig


def _same_origin(left: str, right: str) -> bool:
    default_ports = {"http": 80, "https": 443}
    left_url = urlsplit(left)
    right_url = urlsplit(right)
    left_origin = (
        left_url.scheme.lower(),
        left_url.hostname,
        left_url.port or default_ports.get(left_url.scheme.lower()),
    )
    right_origin = (
        right_url.scheme.lower(),
        right_url.hostname,
        right_url.port or default_ports.get(right_url.scheme.lower()),
    )
    return left_origin == right_origin


def write_maven_settings(path: Path, repository: RepositoryConfig) -> None:
    mirror = ""
    mirror_id = "sdk-mirror"
    if repository.repository_id and _same_origin(repository.repository_url, repository.mirror_url):
        mirror_id = repository.repository_id
    if repository.mirror_url:
        mirror = (
            f"<mirrors><mirror><id>{escape(mirror_id)}</id><mirrorOf>*</mirrorOf>"
            f"<url>{escape(repository.mirror_url)}</url></mirror></mirrors>"
        )
    servers = ""
    if repository.repository_id:
        servers = (
            f"<server><id>{escape(repository.repository_id)}</id><username>{escape(repository.username)}</username>"
            f"<password>{escape(repository.password)}</password></server>"
        )
    path.write_text(f"<settings>{mirror}<servers>{servers}</servers></settings>")
    path.chmod(0o600)


__all__ = ["write_maven_settings"]
