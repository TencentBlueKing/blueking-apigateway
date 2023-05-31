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
from blue_krill.cubing_case import shortcuts
from django.conf import settings

from apigateway.apps.support.api_sdk.exceptions import TooManySDKVersion
from apigateway.apps.support.api_sdk.models import SDKContext
from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.apps.support.models import APISDK
from apigateway.core.models import ResourceVersion
from apigateway.utils import time as time_utils


class SDKManagerMixin:
    version: str
    is_public: bool
    language: ProgrammingLanguageEnum

    def get_version(self, resource_version):
        """根据网关和资源版本，生成SDK版本号"""
        count = APISDK.objects.get_resource_version_sdk_count(  # type: ignore
            resource_version.id,
            ProgrammingLanguageEnum.PYTHON.value,
        )
        if count >= settings.MAX_PYTHON_SDK_COUNT_PER_RESOURCE_VERSION:
            raise TooManySDKVersion(settings.MAX_PYTHON_SDK_COUNT_PER_RESOURCE_VERSION)

        # 用户已指定版本，直接返回
        if self.version:
            return self.version

        suffix = str(count + 1).rjust(2, "0")
        created_time_str = time_utils.format(resource_version.created_time, fmt="YYYYMMDDHHmmss")
        return f"{created_time_str}{suffix}"

    def get_is_latest(self, resource_version):
        return APISDK.objects.should_be_set_to_public_latest(  # type: ignore
            resource_version.api,
            resource_version.id,
            self.is_public,
        )

    def get_context(self, resource_version: ResourceVersion) -> SDKContext:
        api_name = resource_version.api.name

        return SDKContext(
            name=f"bkapi-{ shortcuts.to_lower_dash_case(api_name) }",
            package=api_name,
            resource_version=resource_version,
            language=self.language,
            is_public=self.is_public,
            version=self.get_version(resource_version),
            is_latest=self.get_is_latest(resource_version),
        )
