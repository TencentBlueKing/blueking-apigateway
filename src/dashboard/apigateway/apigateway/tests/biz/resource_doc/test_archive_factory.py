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
import pytest

from apigateway.biz.resource_doc.archive_factory import ArchiveFileFactory
from apigateway.utils.archivefile import TgzArchiveFile, ZipArchiveFile


class TestArchiveFileFactory:
    def test_from_file_type(self):
        result = ArchiveFileFactory.from_file_type("tgz")
        assert isinstance(result, TgzArchiveFile)

        result = ArchiveFileFactory.from_file_type("zip")
        assert isinstance(result, ZipArchiveFile)

        with pytest.raises(ValueError):
            ArchiveFileFactory.from_file_type("unknown")

    def test_from_fileobj(self, fake_tgz_file, fake_zip_file):
        result = ArchiveFileFactory.from_fileobj(fake_tgz_file)
        assert isinstance(result, TgzArchiveFile)

        result = ArchiveFileFactory.from_fileobj(fake_zip_file)
        assert isinstance(result, ZipArchiveFile)

    def test_guess_file_type(self, fake_tgz_file, fake_zip_file, fake_text_file):
        result = ArchiveFileFactory._guess_file_type(fake_tgz_file)
        assert result == "tgz"

        result = ArchiveFileFactory._guess_file_type(fake_zip_file)
        assert result == "zip"

        result = ArchiveFileFactory._guess_file_type(fake_text_file)
        assert result == "unknown"
