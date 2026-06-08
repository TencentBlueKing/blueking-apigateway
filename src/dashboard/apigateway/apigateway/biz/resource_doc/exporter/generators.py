#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import logging
import os
from typing import Dict, List

from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.biz.resource_doc import NoResourceDocError
from apigateway.core.models import Resource, ResourceVersion
from apigateway.utils.file import write_to_file

logger = logging.getLogger(__name__)


class DocArchiveGenerator:
    def generate(
        self,
        output_dir: str,
        gateway_id: int,
        resource_ids: List[int],
    ) -> List[str]:
        resource_id_to_name = dict(
            Resource.objects.filter(gateway_id=gateway_id, id__in=resource_ids).values_list("id", "name")
        )

        files = []
        queryset = ResourceDoc.objects.filter(gateway_id=gateway_id, resource_id__in=resource_ids)
        for resource_doc in queryset:
            resource_name = resource_id_to_name.get(resource_doc.resource_id)
            if not resource_name:
                continue

            dirname = os.path.join(output_dir, resource_doc.language)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            filename = f"{resource_doc.language}/{resource_name}.md"
            write_to_file(resource_doc.content, os.path.join(output_dir, filename))
            files.append(filename)

        if not files:
            raise NoResourceDocError()

        return files


class ResourceVersionDocArchiveGenerator:
    """从 ResourceDocVersion 的快照数据生成文档归档文件"""

    def generate(
        self,
        output_dir: str,
        resource_version: ResourceVersion,
    ) -> List[str]:
        """根据资源版本对应的文档版本快照生成文档文件

        :param output_dir: 输出目录
        :param resource_version: 资源版本实例
        :return: 生成的文件路径列表（相对于 output_dir）
        """
        # 查询对应的文档版本
        try:
            doc_version = ResourceDocVersion.objects.get(
                gateway=resource_version.gateway,
                resource_version=resource_version,
            )
        except ResourceDocVersion.DoesNotExist:
            raise NoResourceDocError()

        doc_data = doc_version.data
        if not doc_data:
            raise NoResourceDocError()

        # 从 resource_version.data 构建 resource_id -> resource_name 映射
        resource_id_to_name: Dict[int, str] = {resource["id"]: resource["name"] for resource in resource_version.data}

        return self._generate_docs(output_dir, doc_data, resource_id_to_name)

    def _generate_docs(
        self,
        output_dir: str,
        doc_data: list,
        resource_id_to_name: Dict[int, str],
    ) -> List[str]:
        files = []
        for doc in doc_data:
            resource_id = doc.get("resource_id")
            resource_name = resource_id_to_name.get(resource_id)
            if not resource_name:
                logger.warning("resource_id %s not found in resource_id_to_name, skip doc generation", resource_id)
                continue

            language = doc.get("language", "zh")
            content = doc.get("content", "")

            dirname = os.path.join(output_dir, language)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            filename = f"{language}/{resource_name}.md"
            write_to_file(content, os.path.join(output_dir, filename))
            files.append(filename)

        if not files:
            raise NoResourceDocError()

        return files
