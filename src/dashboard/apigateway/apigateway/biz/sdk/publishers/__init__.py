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

from . import maven, pypi
from .common import PublishedArtifact

if TYPE_CHECKING:
    from apigateway.biz.sdk.artifacts import BuiltArtifact
    from apigateway.biz.sdk.config import SDKLanguageConfig


def publish_native(
    language: str,
    artifacts: list[BuiltArtifact],
    language_config: SDKLanguageConfig,
) -> list[PublishedArtifact]:
    if language != language_config.language:
        raise ValueError("native publisher language does not match its configuration")
    if language_config.native_distributor is None:
        return []
    if language == "python" and language_config.native_distributor == "pypi":
        return pypi.publish(artifacts, language_config)
    if language == "java" and language_config.native_distributor == "maven":
        return maven.publish(artifacts, language_config)
    raise ValueError(f"unsupported native SDK publisher: {language_config.native_distributor}")


__all__ = ["PublishedArtifact", "publish_native"]
