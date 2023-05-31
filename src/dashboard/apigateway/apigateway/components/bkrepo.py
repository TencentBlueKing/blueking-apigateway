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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from blue_krill.storages.blobstore.base import SignatureType
from blue_krill.storages.blobstore.bkrepo import BKGenericRepo
from django.conf import settings


@dataclass
class BKRepoComponent:
    endpoint_url: str
    username: str
    password: str
    project: str
    generic_bucket: str

    _generic_client: BKGenericRepo = field(init=False)

    def __post_init__(self):
        self._generic_client = BKGenericRepo(
            bucket=self.generic_bucket,
            project=self.project,
            endpoint_url=self.endpoint_url,
            username=self.username,
            password=self.password,
        )

    def upload_generic_file(self, filepath: str, key: str, allow_overwrite: bool = True):
        """上传通用制品文件"""
        self._generic_client.upload_file(filepath=Path(filepath), key=key, allow_overwrite=allow_overwrite)

    def generate_generic_download_url(self, key: str, expires_in: int = 0) -> str:
        """创建专用下载 url"""

        return self._generic_client.generate_presigned_url(
            key, expires_in=expires_in, signature_type=SignatureType.DOWNLOAD
        )

    @classmethod
    def default(cls) -> Optional["BKRepoComponent"]:
        if not settings.BKREPO_ENDPOINT_URL:
            return None

        return cls(
            endpoint_url=settings.BKREPO_ENDPOINT_URL,
            username=settings.BKREPO_USERNAME,
            password=settings.BKREPO_PASSWORD,
            project=settings.BKREPO_PROJECT,
            generic_bucket=settings.BKREPO_GENERIC_BUCKET,
        )
