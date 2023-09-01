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
import os

from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.support.api_sdk.helper import SDKHelper
from apigateway.core.models import Gateway, ResourceVersion


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--api_name", type=str, dest="api_name", required=True, help="API Name")
        parser.add_argument("--resource_version", type=str, dest="resource_version", required=True)
        parser.add_argument("--language", required=True)
        parser.add_argument("--include_private_resources", default=False)
        parser.add_argument("--is_public", default=False)
        parser.add_argument("--sdk_version", default=False)
        parser.add_argument("--operator", default=False)
        parser.add_argument("--output_dir", default="./sdks/")

    def handle(
        self,
        api_name,
        resource_version,
        language,
        output_dir,
        include_private_resources,
        is_public,
        sdk_version,
        operator,
        *args,
        **options,
    ):
        gateway = Gateway.objects.filter(name=api_name).first()
        if not gateway:
            raise CommandError(f"网关{api_name}不存在")

        resource_version = ResourceVersion.objects.get(api=gateway, name=resource_version)
        if not resource_version:
            raise CommandError(f"版本{resource_version}不存在")

        version = sdk_version or resource_version.version

        os.makedirs(output_dir, exist_ok=True)
        with SDKHelper(resource_version=resource_version, output_dir=output_dir) as helper:
            context = helper.create_context(
                language=language,
                version=version,
            )

        if context.files:
            print("generated: ", ",".join(context.files))

        if context.url:
            print("url: ", context.url)
