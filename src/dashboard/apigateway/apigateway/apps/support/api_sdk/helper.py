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
import os
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Dict, Optional

from apigateway.apps.support.api_sdk.managers import SDKManagerFactory
from apigateway.apps.support.api_sdk.models import SDKContext
from apigateway.apps.support.models import GatewaySDK
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import ResourceVersion
from apigateway.utils import time as time_utils


@dataclass
class SDKInfo:
    context: SDKContext
    sdk: GatewaySDK

    def get_packaged_files(self) -> Dict[str, str]:
        return {os.path.basename(file_path): file_path for file_path in self.context.files}


@dataclass
class SDKHelper:
    resource_version: ResourceVersion
    output_dir: str = ""
    temporary_dir: Optional[TemporaryDirectory] = None

    def __post_init__(self):
        if self.output_dir:
            return

        if not self.temporary_dir:
            self.temporary_dir = TemporaryDirectory()

        self.output_dir = self.temporary_dir.name

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        if self.temporary_dir:
            self.temporary_dir.cleanup()

    def create_context(
        self,
        language: str,
        version: str,
        include_private_resources: bool,
        is_public: bool,
    ) -> SDKContext:
        resource_version = self.resource_version
        manager = SDKManagerFactory.create(
            language,
            version=version,
            include_private_resources=include_private_resources,
            is_public=is_public,
        )
        return manager.handle(self.output_dir, resource_version)

    def create(
        self,
        language: str,
        version: str,
        operator: Optional[str],
    ) -> SDKInfo:
        # NOTE: we want the sdk contains all apis, including private ones
        include_private_resources = True
        # NOTE: it's always be True from 1.13, we try to make the sdks all public! (no private anymore)
        # but maybe rolling back, so keep the private sdk logical for now
        is_public = True

        context = self.create_context(
            language=language,
            version=version,
            # those args will make the sdk distributed in public or private
            include_private_resources=include_private_resources,
            is_public=is_public,
        )

        now = time_utils.now_datetime()
        # `instance` is a `APISDK` object.
        instance = GatewaySDK.objects.create(
            gateway=context.resource_version.gateway,
            resource_version=context.resource_version,
            language=context.language.value,
            version_number=context.version,
            name=context.name,
            url=context.url,
            include_private_resources=include_private_resources,
            is_public=is_public,
            schema=SchemaFactory().get_api_sdk_schema(),
            config=context.config,
            created_time=now,
            updated_time=now,
            created_by=operator,
        )

        if instance.is_public and context.is_latest:
            instance.mark_is_recommended()

        return SDKInfo(context=context, sdk=instance)
