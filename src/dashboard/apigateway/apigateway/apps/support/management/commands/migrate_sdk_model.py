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

from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from tencent_apigateway_common.pypi.registry import SimplePypiRegistry

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.apps.support.models import APISDK
from apigateway.utils.pypi import RepositoryConfig


class Command(BaseCommand):
    repository = "tencent"
    pypi_config = RepositoryConfig.by_name(repository)
    filename_re = re.compile(r"(?P<package>bkapigw.(?P<name>.*?))-\w+.tar.gz")

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", default=False, action="store_true")

    def update_is_recommended(self, sdk: APISDK):
        if sdk.is_public_latest:
            print(f"mark {sdk} is recommended")
            sdk.is_recommended = True
        else:
            sdk.is_recommended = False

        return True

    def update_is_public(self, sdk: APISDK):
        config = sdk.config.get(ProgrammingLanguageEnum.PYTHON.value, {})
        if config.get("is_uploaded_to_pypi"):
            print(f"mark {sdk} is public")
            sdk.is_public = True
        else:
            sdk.is_public = False

        return True

    def update_name_and_url(self, sdk: APISDK):
        if not sdk.filename:
            return True

        matched = self.filename_re.search(sdk.filename)
        if not matched:
            return False

        grouped = matched.groupdict()
        name = grouped["package"]
        sdk.name = name

        print(f"{sdk} name is {name}")

        if not sdk.is_public:
            return True

        registry = SimplePypiRegistry(self.pypi_config.index_url)
        package = grouped["package"].replace(".", "-")
        result = registry.search(package, sdk.version_number)
        if not result:
            return False

        sdk.url = result.url
        print(f"{sdk} url is {result.url}")
        return True

    def update_repository(self, sdk: APISDK):
        if not sdk.is_public:
            return True

        config = sdk.config
        language_config = config.setdefault(ProgrammingLanguageEnum.PYTHON.value, {})
        language_config["repository"] = self.repository
        sdk.config = config

        print(f"{sdk} repository is {self.repository}")
        return True

    def update_sdk(self, sdk: APISDK, dry_run: bool):
        if sdk.name:
            print(f"skip the new sdk object: {sdk}")
            return True

        if not all(
            [
                self.update_is_recommended(sdk),
                self.update_is_public(sdk),
                self.update_name_and_url(sdk),
                self.update_repository(sdk),
            ]
        ):
            return False

        if not dry_run:
            sdk.save(
                update_fields=[
                    "name",
                    "is_recommended",
                    "is_public",
                    "url",
                    "_config",
                ],
            )

        return True

    @atomic
    def handle(self, dry_run, *args, **options):
        fails = []
        for sdk in APISDK.objects.all():
            try:
                if not self.update_sdk(sdk, dry_run):
                    fails.append(sdk.pk)
            except Exception as e:
                print(e)
                fails.append(sdk.pk)

        print(f"migrate fails: {fails}")
