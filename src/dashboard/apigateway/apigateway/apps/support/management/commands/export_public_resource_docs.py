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
"""
导出指定网关的资源文档
"""
import os
from tempfile import TemporaryDirectory
from typing import Dict, List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.support.constants import DocArchiveTypeEnum
from apigateway.apps.support.resource_doc.exceptions import NoResourceDocError
from apigateway.apps.support.resource_doc.export_doc.generators import DocArchiveGenerator
from apigateway.apps.support.utils import ArchiveFileFactory
from apigateway.core.constants import APIStatusEnum
from apigateway.core.models import Gateway, Resource


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--api-names", dest="api_names", type=str, nargs="*")
        parser.add_argument("--file-type", dest="file_type", default="tgz", choices=DocArchiveTypeEnum.get_values())
        parser.add_argument("--output", dest="output", type=str, help="output filename")

    def handle(self, api_names: List[str], file_type: str, output: str, **options) -> None:
        output = self._validate_output(output, file_type)
        gateway_name_to_id = self._get_export_gateways(api_names)
        archivefile = ArchiveFileFactory.from_file_type(file_type)

        doc_files = []
        with TemporaryDirectory() as temp_dir:
            for gateway_name, gateway_id in gateway_name_to_id.items():
                doc_dir = os.path.join(temp_dir, gateway_name)
                os.makedirs(doc_dir)
                try:
                    files = DocArchiveGenerator().generate(
                        doc_dir,
                        gateway_id,
                        resource_ids=Resource.objects.filter_public_resource_ids(gateway_id),
                    )
                except NoResourceDocError:
                    os.rmdir(doc_dir)
                    continue

                doc_files.extend([f"{gateway_name}/{name}" for name in files])

            if not os.listdir(temp_dir):
                raise CommandError("网关不存在资源文档，导出失败")

            archive_path = archivefile.archive(temp_dir, "bk_apigw_docs.{file_tpye}", doc_files)
            os.rename(archive_path, output)

    def _validate_output(self, output: str, file_type: str):
        if not output:
            return os.path.join(settings.BASE_DIR, f"bk_apigw_docs.{file_type}")

        dirname = os.path.dirname(output)
        if not os.path.exists(dirname):
            raise CommandError(f"output dir does not exist: {dirname}")

        return output

    def _get_export_gateways(self, gateway_names: List[str]) -> Dict[str, int]:
        gateway_name_to_id = dict(
            Gateway.objects.filter(status=APIStatusEnum.ACTIVE.value, is_public=True).values_list("name", "id")
        )

        if not gateway_names:
            return gateway_name_to_id

        not_exist_api = set(gateway_names) - set(gateway_name_to_id.keys())
        if not_exist_api:
            raise CommandError(f"以下网关不存在，请检查：{', '.join(sorted(list(not_exist_api)))}")

        return {name: gateway_name_to_id[name] for name in gateway_names}
