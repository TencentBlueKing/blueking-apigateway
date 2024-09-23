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

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.conf import settings


class OpenAPIFormatEnum(StructuredEnum):
    YAML = EnumField("yaml", label="YAML")
    JSON = EnumField("json", label="JSON")


# bk app code
APP_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")

# Semver
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

MAX_BACKEND_TIMEOUT_IN_SECOND = settings.MAX_BACKEND_TIMEOUT_IN_SECOND

# stage var
STAGE_VAR_FOR_PATH_PATTERN = re.compile(r"^[\w/.-]*$")
