#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

from blue_krill.data_types.enum import EnumField, StructuredEnum
from packaging.version import InvalidVersion, Version


class DataPlaneStatusEnum(StructuredEnum):
    """Data Plane status enum"""

    ACTIVE = EnumField(1, "active")
    INACTIVE = EnumField(0, "inactive")


class DataPlaneApisixVersionEnum(StructuredEnum):
    """APISIX version of the data plane deployment"""

    V3_13 = EnumField("3.13", "3.13")
    V3_16 = EnumField("3.16", "3.16")


CURRENT_DATA_PLANE_APISIX_VERSION = DataPlaneApisixVersionEnum.V3_16.value
AI_GATEWAY_MIN_APISIX_VERSION = DataPlaneApisixVersionEnum.V3_16.value


def is_apisix_version_supported_for_ai_gateway(apisix_version: str) -> bool:
    try:
        return Version(apisix_version) >= Version(AI_GATEWAY_MIN_APISIX_VERSION)
    except InvalidVersion, TypeError:
        return False


class BkPluginsDataPlaneGrayStageEnum(StructuredEnum):
    """Gray stage for BK plugins data plane migration"""

    NOT_START = EnumField("not_start", "not_start")
    START = EnumField("start", "start")
    DONE = EnumField("done", "done")


# Default data plane name
DEFAULT_DATA_PLANE_NAME = "default"
