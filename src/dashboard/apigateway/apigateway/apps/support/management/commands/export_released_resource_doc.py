# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
导出某个网关某个已发布版本的资源文档
"""

import os
import shutil
from tempfile import TemporaryDirectory
from typing import Dict, List

from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.support.constants import DocArchiveTypeEnum, DocLanguageEnum
from apigateway.apps.support.models import ResourceDocVersion
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.utils.archivefile import TgzArchiveFile, ZipArchiveFile
from apigateway.utils.file import write_to_file


class Command(BaseCommand):
    help = "导出某个网关某个已发布版本的资源文档"

    def add_arguments(self, parser):
        parser.add_argument("--gateway-name", type=str, required=True, help="网关名称")
        parser.add_argument("--resource-version", type=str, required=True, help="资源版本号")
        parser.add_argument("--output", type=str, required=True, help="输出文件路径")
        parser.add_argument(
            "--file-type",
            type=str,
            default=DocArchiveTypeEnum.ZIP.value,
            choices=[DocArchiveTypeEnum.ZIP.value, DocArchiveTypeEnum.TGZ.value],
            help="导出文件类型",
        )

    def handle(self, *args, **options):
        gateway_name = options["gateway_name"]
        version = options["resource_version"]
        output = options["output"]
        file_type = options["file_type"]

        gateway = Gateway.objects.filter(name=gateway_name).first()
        if not gateway:
            raise CommandError(f"Gateway not found: {gateway_name}")

        resource_version = ResourceVersion.objects.filter(gateway=gateway, version=version).first()
        if not resource_version:
            raise CommandError(f"ResourceVersion not found: {version}")

        resource_doc_version = ResourceDocVersion.objects.filter(
            gateway=gateway, resource_version=resource_version
        ).first()
        if not resource_doc_version:
            raise CommandError(f"ResourceDocVersion not found for gateway={gateway_name}, version={version}")

        resource_id_to_name = {
            resource["id"]: resource["name"]
            for resource in resource_version.data
            if resource.get("id") and resource.get("name")
        }

        with TemporaryDirectory() as output_dir:
            files = self._generate_docs(output_dir, resource_doc_version, resource_id_to_name)

            if not files:
                raise CommandError("No resource docs found for this version")

            archive_name = f"bk_apigw_docs_{gateway_name}_{version}.{file_type}"
            if file_type == DocArchiveTypeEnum.TGZ.value:
                archivefile = TgzArchiveFile()
            elif file_type == DocArchiveTypeEnum.ZIP.value:
                archivefile = ZipArchiveFile()
            else:
                raise CommandError(f"unsupported file_type: {file_type}")
            archive_path = archivefile.archive(output_dir, archive_name, files)

            output_dir_path = os.path.dirname(output)
            if output_dir_path and not os.path.exists(output_dir_path):
                os.makedirs(output_dir_path)

            shutil.copy(archive_path, output)

        self.stdout.write(self.style.SUCCESS(f"Successfully exported {len(files)} resource docs to {output}"))

    def _generate_docs(
        self,
        output_dir: str,
        resource_doc_version: ResourceDocVersion,
        resource_id_to_name: Dict[int, str],
    ) -> List[str]:
        files = []
        for doc in resource_doc_version.data:
            resource_id = doc.get("resource_id")
            language = doc.get("language", DocLanguageEnum.ZH.value)
            content = doc.get("content", "")

            resource_name = resource_id_to_name.get(resource_id)
            if not resource_name:
                self.stdout.write(
                    self.style.WARNING(f"Resource name not found for resource_id={resource_id}, skipping")
                )
                continue

            dirname = os.path.join(output_dir, language)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            filename = f"{language}/{resource_name}.md"
            write_to_file(content, os.path.join(output_dir, filename))
            files.append(filename)

        return files
