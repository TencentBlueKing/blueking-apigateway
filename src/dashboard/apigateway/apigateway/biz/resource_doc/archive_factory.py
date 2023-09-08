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
import tarfile
import zipfile

from apigateway.apps.support.constants import DocArchiveTypeEnum
from apigateway.utils.archivefile import BaseArchiveFile, TgzArchiveFile, ZipArchiveFile


class ArchiveFileFactory:
    @classmethod
    def from_file_type(cls, file_type: str) -> "BaseArchiveFile":
        if file_type == DocArchiveTypeEnum.TGZ.value:
            return TgzArchiveFile()

        if file_type == DocArchiveTypeEnum.ZIP.value:
            return ZipArchiveFile()

        raise ValueError(f"unsupported file_type: {file_type}")

    @classmethod
    def from_fileobj(cls, fileobj) -> "BaseArchiveFile":
        file_type = cls._guess_file_type(fileobj)
        return cls.from_file_type(file_type)

    @classmethod
    def _guess_file_type(cls, fileobj) -> str:
        if zipfile.is_zipfile(fileobj):
            return DocArchiveTypeEnum.ZIP.value

        if cls._is_tarfile(fileobj):
            return DocArchiveTypeEnum.TGZ.value

        return "unknown"

    @classmethod
    def _is_tarfile(cls, fileobj) -> bool:
        # python 3.8 以下 tarfile.is_tarfile 支持文件名，不支持文件对象
        fileobj.seek(0)

        try:
            t = tarfile.open(fileobj=fileobj)
            t.close()
            return True
        except tarfile.TarError:
            return False
