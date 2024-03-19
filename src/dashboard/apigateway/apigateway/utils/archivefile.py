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
"""文档归档"""

import os
import tarfile
import zipfile
from typing import IO, AnyStr, Dict, Iterable, List


class BaseArchiveFile:
    def archive(self, output_dir: str, archive_name: str, files: Iterable[str]) -> str:
        raise NotImplementedError

    def extractall(self, output_dir: str, fileobj: IO[AnyStr]) -> Dict[str, str]:
        raise NotImplementedError

    def get_names(self, fileobj: IO[AnyStr]) -> List[str]:
        raise NotImplementedError


class ZipArchiveFile(BaseArchiveFile):
    """zip 归档文件"""

    def archive(self, output_dir: str, archive_name: str, files: Iterable[str]) -> str:
        archive_path = os.path.join(output_dir, archive_name)

        with zipfile.ZipFile(archive_path, "x") as zip_:
            for name in files:
                zip_.write(os.path.join(output_dir, name), name)

        return archive_path

    def extractall(self, output_dir: str, fileobj: IO[AnyStr]) -> Dict[str, str]:
        """提取归档文件中的所有文件"""
        fileobj.seek(0)

        with zipfile.ZipFile(fileobj, mode="r") as zip_:  # type: ignore
            zip_.extractall(output_dir)

            # 文档对应文档文件的路径，因并非所有文档都需更新，此处不读取文件内容
            return {
                item.filename: os.path.join(output_dir, item.filename.lstrip("/"))
                for item in zip_.infolist()
                if not item.is_dir()
            }

    def get_names(self, fileobj: IO[AnyStr]) -> List[str]:
        fileobj.seek(0)

        with zipfile.ZipFile(fileobj, mode="r") as zip_:  # type: ignore
            return [item.filename for item in zip_.infolist() if not item.is_dir()]


class TgzArchiveFile(BaseArchiveFile):
    """tgz 归档文件"""

    def archive(self, output_dir: str, archive_name: str, files: Iterable[str]) -> str:
        archive_path = os.path.join(output_dir, archive_name)
        with tarfile.open(name=archive_path, mode="x:gz") as tgz:
            for name in files:
                tgz.add(os.path.join(output_dir, name), name)

        return archive_path

    def extractall(self, output_dir: str, fileobj: IO[AnyStr]) -> Dict[str, str]:
        """提取归档文件中的所有文件"""
        # 上传的 tar.gz 文件如果不 seek，读取到的文件内容为空
        fileobj.seek(0)

        with tarfile.open(fileobj=fileobj, mode="r:*") as tgz:  # type: ignore
            tgz.extractall(output_dir)

            # 文档对应文档文件的路径，因并非所有文档都需更新，此处不读取文件内容
            return {
                item.name: os.path.join(output_dir, item.name.lstrip("/"))
                for item in tgz.getmembers()
                if item.isfile()
            }

    def get_names(self, fileobj: IO[AnyStr]) -> List[str]:
        # 上传的 tar.gz 文件如果不 seek，读取到的文件内容为空
        fileobj.seek(0)

        with tarfile.open(fileobj=fileobj, mode="r:*") as tgz:  # type: ignore
            return [item.name for item in tgz.getmembers() if item.isfile()]
