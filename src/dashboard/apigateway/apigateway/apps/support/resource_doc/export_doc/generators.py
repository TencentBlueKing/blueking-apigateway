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
from typing import List, Optional

from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.resource_doc.exceptions import NoResourceDocError
from apigateway.core.models import Resource
from apigateway.utils.file import write_to_file


class DocArchiveGenerator:
    def generate(
        self,
        output_dir: str,
        gateway_id: int,
        resource_ids: Optional[List[int]] = None,
    ) -> List[str]:
        resource_id_to_name = Resource.objects.get_id_to_name(gateway_id=gateway_id, resource_ids=resource_ids)

        files = []
        for doc in ResourceDoc.objects.filter_docs(gateway_id=gateway_id, resource_ids=resource_ids):
            resource_name = resource_id_to_name.get(doc.resource_id)
            if not resource_name:
                continue

            dirname = os.path.join(output_dir, doc.language)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            filename = f"{doc.language}/{resource_name}.md"
            write_to_file(doc.content, os.path.join(output_dir, filename))
            files.append(filename)

        if not files:
            raise NoResourceDocError

        return files
