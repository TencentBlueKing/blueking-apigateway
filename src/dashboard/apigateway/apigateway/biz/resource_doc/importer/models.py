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
from dataclasses import dataclass
from typing import Optional

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.models import Resource


@dataclass
class BaseDoc:
    resource_name: str
    language: DocLanguageEnum
    content: str
    # we think is changed unless the old and new md5 are the same
    content_changed: bool = True
    # 文档关联的资源
    resource: Optional[Resource] = None
    # 文档关联的资源文档
    resource_doc: Optional[ResourceDoc] = None


@dataclass
class ArchiveDoc(BaseDoc):
    """从归档文件中解析出来文档"""

    filename: str = ""


@dataclass
class SwaggerDoc(BaseDoc):
    """从 Swagger 中解析出来的文档"""

    swagger: str = ""
